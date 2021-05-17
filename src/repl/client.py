from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from inspect import cleandoc
import base64
import queue
import os
import pathlib
import posixpath
import select
import socket

from .backchannel import Backchannel, NoopBackchannel
from ...api import edn
from ..log import log


class Client(ABC):
    def start_workers(self):
        self.executor.submit(self.send_loop)
        self.executor.submit(self.recv_loop)
        self.executor.submit(self.format_loop)
        return self

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.buffer = self.socket.makefile(mode="rw")
        log.debug({"event": "client/connect", "host": self.host, "port": self.port})
        return self

    def disconnect(self):
        if self.socket is not None:
            try:
                self.buffer.close()
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                log.debug({"event": "client/disconnect"})
            except OSError as e:
                log.debug({"event": "error", "exception": e})

    def __init__(self, host, port, name):
        self.host = host
        self.port = port
        self.name = name
        self.sendq = queue.Queue()
        self.recvq = queue.Queue()
        self.printq = queue.Queue()
        self.handlers = {}
        self.executor = ThreadPoolExecutor(thread_name_prefix=f"{self.name}")
        self.namespace = "user"

        self.disconnect_msg = {
            edn.Keyword("tag"): edn.Keyword("ret"),
            edn.Keyword("val"): ":tutkain/disconnected"
        }

    def __enter__(self):
        self.connect()
        return self

    def send_loop(self):
        while item := self.sendq.get():
            log.debug({"event": "client/send", "item": item})
            self.buffer.write(item)
            self.buffer.write("\n")
            self.buffer.flush()

        log.debug({"event": "thread/exit"})

    @abstractmethod
    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        pass

    def handle(self, item):
        if ns := item.get(edn.Keyword("ns")):
            self.namespace = ns

        if (form := item.get(edn.Keyword("form"))) and (handler := self.handlers.get(form)):
            try:
                handler.__call__(item)
            finally:
                self.handlers.pop(form, None)
        else:
            self.recvq.put(item)

    def recv_loop(self):
        try:
            while item := edn.read_line(self.buffer):
                log.debug({"event": "client/recv", "item": item})
                self.handle(item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            if self.disconnect_msg:
                self.recvq.put(self.disconnect_msg)

            # put a None into the queue to tell consumers to stop reading it.
            self.recvq.put(None)

            # Feed poison pill to input queue.
            self.sendq.put(None)

            log.debug({"event": "thread/exit"})

            # We've exited the loop that reads from the socket, so we can
            # close the connection to the socket.
            self.disconnect()

    def format_form(self, form):
        if lines := cleandoc(form).splitlines():
            first_line = (lines[0] + "\n")

            next_lines = "\n".join(
                map(lambda line: ((len(self.namespace) + 5) * " ") + line, lines[1:])
            )

            if next_lines:
                next_lines += "\n"

            return f"""{self.namespace}=> {first_line}{next_lines}"""

    def format(self, response):
        if form := response.get(edn.Keyword("in")):
            return self.format_form(form)

        if val := response.get(edn.Keyword("val")):
            return val.rstrip() + "\n"

        for k in {"out", "err", "ex"}:
            if x := response.get(edn.Keyword(k)):
                return x

    def format_loop(self):
        try:
            log.debug({"event": "thread/start"})

            while response := self.recvq.get():
                log.debug({"event": "formatq/recv", "data": response})

                if printable := self.format(response):
                    self.printq.put({"printable": printable, "response": response})
        finally:
            self.printq.put(None)
            log.debug({"event": "thread/exit"})

    def halt(self):
        log.debug({"event": "client/halt"})
        self.recvq.put(None)
        self.sendq.put(":repl/quit")

    def __exit__(self, type, value, traceback):
        self.halt()


class JVMClient(Client):
    handshake_payloads = {
        "print_version": """#?(:bb (println "Babashka" (System/getProperty "babashka.version")) :clj (println "Clojure" (clojure-version)))"""
    }

    modules = {
        "base": {
            "lookup.clj": [],
            "completions.clj": [],
            "load_blob.clj": [],
            "test.clj": []
        },

        "cljs": {
            "cljs.clj": [edn.Symbol("cljs.core")],
            "shadow.clj": [edn.Symbol("shadow.cljs.devtools.api")]
        }
    }

    def write_line(self, line):
        self.buffer.write(line)
        self.buffer.write("\n")
        self.buffer.flush()

    def sink_all(self):
        bs = bytearray()
        data = self.socket.recv(1024)
        bs.extend(data)

        while data:
            readable, _, _ = select.select([self.socket], [], [], 0)

            if self.socket in readable:
                data = readable[0].recv(1024)
                bs.extend(data)
            else:
                break

        return bs

    def cljs_module_loaded(self, response, on_done):
        filename = response.get(edn.Keyword("filename"))
        self.attempted_modules.add(filename)

        if response.get(edn.Keyword("result")) == edn.Keyword("ok"):
            self.capabilities.add(filename)

        if len(self.attempted_modules) == len(self.modules["cljs"].keys()):
            self.ready_for_cljs = True
            on_done()

    def load_cljs_modules(self, on_done=lambda: None):
        for filename, requires in self.modules["cljs"].items():
            path = os.path.join(self.source_root, filename)

            with open(path, "rb") as file:
                self.backchannel.send({
                    "op": edn.Keyword("load-base64"),
                    "path": path,
                    "filename": filename,
                    "blob": base64.b64encode(file.read()).decode("utf-8"),
                    "requires": requires
                }, lambda response: self.cljs_module_loaded(response, on_done))

    def base_module_loaded(self, response):
        filename = response.get(edn.Keyword("filename"))

        if response.get(edn.Keyword("result")) == edn.Keyword("ok"):
            self.capabilities.add(filename)

    def load_modules(self):
        for filename, requires in self.modules["base"].items():
            path = os.path.join(self.source_root, filename)

            with open(path, "rb") as file:
                self.backchannel.send({
                    "op": edn.Keyword("load-base64"),
                    "path": path,
                    "filename": filename,
                    "blob": base64.b64encode(file.read()).decode("utf-8"),
                    "requires": requires
                }, self.base_module_loaded)

    def handshake(self):
        log.debug({"event": "client/handshake", "data": self.sink_all()})
        path = posixpath.join(pathlib.Path(self.source_root).as_posix(), "repl.clj")

        with open(path, "rb") as file:
            blob = base64.b64encode(file.read()).decode("utf-8")
            backchannel_port = self.backchannel_opts.get("port", 0)
            self.write_line(f"""#?(:bb (do (prn {{:tag :ret :val "{{}}"}}) ((requiring-resolve 'clojure.core.server/io-prepl))) :clj (do (with-open [reader (-> (java.util.Base64/getDecoder) (.decode "{blob}") (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader "{path}" "{os.path.basename(path)}")) (try (tutkain.repl/repl {{:port {backchannel_port}}}) (catch Exception ex {{:tag :err :val (.toString ex)}}))))""")

        line = self.buffer.readline()

        if not line.startswith('{'):
            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("out"),
                "val": "Tutkain failed to start. Here's why:"
            }))

            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": line
            }))

            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("out"),
                "val": "NOTE: Tutkain requires Clojure 1.10.0 or newer."
            }))
        else:
            ret = edn.read(line)

            if (host := ret.get(edn.Keyword("host"))):
                port = ret.get(edn.Keyword("port"))
                self.backchannel = Backchannel(host, port).connect()
            elif (val := edn.read(ret.get(edn.Keyword("val")))) and isinstance(val, dict):
                host = val.get(edn.Keyword("host"))
                port = val.get(edn.Keyword("port"))
                self.backchannel = Backchannel(host, port).connect()
            else:
                self.recvq.put(ret)

        self.load_modules()
        self.write_line(self.handshake_payloads["print_version"])
        self.recvq.put(edn.read_line(self.buffer))

        log.debug({"event": "client/handshake", "data": self.buffer.readline()})

        return True

    def connect(self):
        super(JVMClient, self).connect()
        handshake = self.executor.submit(self.handshake)
        handshake.add_done_callback(lambda _: self.start_workers())

        if self.wait:
            handshake.result(self.wait)

        return self

    def __init__(self, source_root, host, port, backchannel_opts={}, wait=5):
        super(JVMClient, self).__init__(host, port, "tutkain.clojure.client")
        self.source_root = source_root
        self.backchannel = NoopBackchannel()
        self.backchannel_opts = backchannel_opts
        self.wait = wait
        self.capabilities = set()
        self.attempted_modules = set()
        self.ready_for_cljs = False

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.recvq.put

        self.backchannel.send({
            "op": edn.Keyword("set-eval-context"),
            "file": file,
            "line": line + 1,
            "column": column + 1
        }, lambda _: self.sendq.put(code))

    def halt(self):
        super(JVMClient, self).halt()
        self.backchannel.halt()


class JSClient(Client):
    def __init__(self, host, port):
        super(JSClient, self).__init__(host, port, "tutkain.cljs.client")
        self.disconnect_msg = None

    def connect(self):
        super(JSClient, self).connect()
        self.start_workers()
        return self

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.recvq.put
        self.sendq.put(code)
