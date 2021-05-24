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

    def sink_until_prompt(self):
        bs = bytearray()
        poller = select.poll()
        poller.register(self.socket, select.POLLIN)

        while True:
            for _, event in poller.poll():
                if event == select.POLLIN:
                    bs.extend(self.socket.recv(32))

            if bs[-3:] == bytearray(b"=> "):
                break

        return bs

    def write_line(self, line):
        self.buffer.write(line)
        self.buffer.write("\n")
        self.buffer.flush()

    def module_loaded(self, response):
        if response.get(edn.Keyword("result")) == edn.Keyword("ok"):
            self.capabilities.add(response.get(edn.Keyword("filename")))

    def load_modules(self, modules):
        for filename in modules:
            path = os.path.join(self.source_root, filename)

            with open(path, "rb") as file:
                self.backchannel.send({
                    "op": edn.Keyword("load-base64"),
                    "path": path,
                    "filename": filename,
                    "blob": base64.b64encode(file.read()).decode("utf-8")
                }, self.module_loaded)

    @abstractmethod
    def handshake(self):
        pass

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.buffer = self.socket.makefile(mode="rw")

        log.debug({"event": "client/connect", "host": self.host, "port": self.port})

        handshake = self.executor.submit(self.handshake)
        handshake.add_done_callback(lambda _: self.start_workers())

        if self.wait:
            handshake.result(self.wait)

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

    def source_path(self, filename):
        return posixpath.join(pathlib.Path(self.source_root).as_posix(), filename)

    def __init__(self, source_root, host, port, name, wait=5, backchannel_opts={}):
        self.source_root = source_root
        self.host = host
        self.port = port
        self.name = name
        self.sendq = queue.Queue()
        self.recvq = queue.Queue()
        self.printq = queue.Queue()
        self.handlers = {}
        self.executor = ThreadPoolExecutor(thread_name_prefix=f"{self.name}")
        self.namespace = "user"
        self.wait = wait
        self.backchannel = NoopBackchannel()
        self.backchannel_opts = backchannel_opts
        self.capabilities = set()

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

    @abstractmethod
    def switch_namespace(self, ns):
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
            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("ret"),
                "val": ":tutkain/disconnected"
            }))

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

    @abstractmethod
    def format(self, response):
        pass

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
    def handshake(self):
        log.debug({"event": "client/handshake", "data": self.sink_until_prompt()})

        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line('(clojure.main/repl :prompt (constantly "") :need-prompt (constantly false))')
        self.write_line("(ns tutkain.bootstrap)")
        self.buffer.readline()
        self.write_line("(def load-base64 (let [decoder (java.util.Base64/getDecoder)] (fn [blob file filename] (with-open [reader (-> decoder (.decode blob) (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader file filename)))))")
        self.buffer.readline()

        for filename in ["format.clj", "backchannel.clj", "repl.clj"]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.b64encode(file.read()).decode("utf-8")
                self.write_line(f"""(load-base64 "{blob}" "{path}" "{os.path.basename(path)}")""")

            self.buffer.readline()

        backchannel_port = self.backchannel_opts.get("port", 0)
        self.write_line(f"""(try (tutkain.repl/repl {{:port {backchannel_port}}}) (catch Exception ex {{:tag :err :val (.toString ex)}}))""")
        line = self.buffer.readline()

        if not line.startswith('{'):
            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "Couldn't connect to Clojure REPL."
            }))

            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": line
            }))

            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
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

        self.load_modules([
            "lookup.clj",
            "completions.clj",
            "load_blob.clj",
            "test.clj"
        ])

        self.write_line("""(println "Clojure" (clojure-version))""")
        self.recvq.put(edn.read_line(self.buffer))

        log.debug({"event": "client/handshake", "data": self.buffer.readline()})

        return True

    def __init__(self, source_root, host, port, wait=5, backchannel_opts={}):
        super(JVMClient, self).__init__(source_root, host, port, "tutkain.clojure.client", wait=wait, backchannel_opts=backchannel_opts)

    def switch_namespace(self, ns):
        code = f"(do (or (some->> '{ns} find-ns ns-name in-ns) (ns {ns})) (set! *3 *2) (set! *2 *1))"
        self.handlers[code] = lambda _: None
        self.sendq.put(code)

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.recvq.put

        self.backchannel.send({
            "op": edn.Keyword("set-eval-context"),
            "file": file,
            "line": line + 1,
            "column": column + 1
        }, lambda _: self.sendq.put(code))

    def format(self, response):
        if form := response.get(edn.Keyword("in")):
            return self.format_form(form)
        elif val := response.get(edn.Keyword("val")):
            return val

    def halt(self):
        super(JVMClient, self).halt()
        self.backchannel.halt()


class JSClient(Client):
    def __init__(self, source_root, host, port, prompt_for_build_id):
        super(JSClient, self).__init__(source_root, host, port, "tutkain.cljs.client", wait=False)
        self.prompt_for_build_id = prompt_for_build_id

    def handshake(self):
        log.debug({"event": "client/handshake", "data": self.sink_until_prompt()})

        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line('(clojure.main/repl :prompt (constantly "") :need-prompt (constantly false))')
        self.write_line("(ns tutkain.bootstrap)")
        self.buffer.readline()
        self.write_line("(def load-base64 (let [decoder (java.util.Base64/getDecoder)] (fn [blob file filename] (with-open [reader (-> decoder (.decode blob) (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader file filename)))))")
        self.buffer.readline()

        for filename in ["format.clj", "backchannel.clj", "shadow.clj"]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.b64encode(file.read()).decode("utf-8")
                self.write_line(f"""(load-base64 "{blob}" "{path}" "{os.path.basename(path)}")""")

            self.buffer.readline()

        backchannel_port = self.backchannel_opts.get("port", 0)
        self.write_line(f"""(try (tutkain.shadow/repl {{:port {backchannel_port}}}) (catch Exception ex {{:tag :err :val (.toString ex)}}))""")
        build_id_options = edn.read_line(self.buffer)

        self.prompt_for_build_id(
            build_id_options,
            lambda build_id: edn.write(self.buffer, build_id)
        )

        line = self.buffer.readline()
        val = edn.read(line)
        host = val.get(edn.Keyword("host"))
        port = val.get(edn.Keyword("port"))
        self.backchannel = Backchannel(host, port).connect()

        self.load_modules([
            "lookup.clj",
            "completions.clj",
            "cljs.clj",
            "shadow.clj",
        ])

        self.write_line("""(println "ClojureScript" *clojurescript-version*)""")
        line = self.buffer.readline()

        if not line.startswith('{'):
            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "Couldn't connect to ClojureScript REPL. Here's why:"
            }))

            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": line
            }))

            self.recvq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "Is the shadow-cljs watch running for the build ID you chose?"
            }))
        else:
            ret = edn.read(line)
            self.handle(ret)

            if ret.get(edn.Keyword("tag")) != edn.Keyword("err"):
                self.handle(edn.read_line(self.buffer))
                log.debug({"event": "client/handshake", "data": self.buffer.readline()})

        return True

    def switch_namespace(self, ns):
        code = f"(in-ns '{ns})"
        self.handlers[code] = lambda _: None
        self.sendq.put(code)

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.recvq.put
        self.sendq.put(code)

    def format(self, response):
        if form := response.get(edn.Keyword("in")):
            return self.format_form(form)
        elif response.get(edn.Keyword("tag")) == edn.Keyword("out"):
            return response.get(edn.Keyword("val"))
        elif val := response.get(edn.Keyword("val")):
            return val


class BabashkaClient(Client):
    def __init__(self, source_root, host, port):
        super().__init__(source_root, host, port, "tutkain.bb.client", wait=False)

    def handshake(self):
        log.debug({"event": "client/handshake", "data": self.sink_until_prompt()})
        self.write_line(f"""((requiring-resolve 'clojure.core.server/io-prepl))""")
        self.write_line("""(println "Babashka" (System/getProperty "babashka.version"))""")
        self.recvq.put(edn.read_line(self.buffer))
        self.buffer.readline()
        return True

    def switch_namespace(self, ns):
        code = f"(in-ns '{ns})"
        self.handlers[code] = lambda _: None
        self.sendq.put(code)

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.recvq.put
        self.sendq.put(code)

    def format(self, response):
        if form := response.get(edn.Keyword("in")):
            return self.format_form(form)
        elif response.get(edn.Keyword("tag")) == edn.Keyword("out"):
            return response.get(edn.Keyword("val"))
        elif val := response.get(edn.Keyword("val")):
            return val + "\n"
