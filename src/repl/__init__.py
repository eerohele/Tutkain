from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
import queue
import os
import pathlib
import posixpath
import socket
import types

from . import backchannel
from ...api import edn
from ..log import log
from .. import base64


def read_until_prompt(socket: socket.SocketType):
    """Given a socket, read bytes from the socket until `=> `, then return the
    read bytes."""
    bs = bytearray()

    while bs[-3:] != bytearray(b"=> "):
        bs.extend(socket.recv(1))

    return bs


class Client(ABC):
    """A `Client` connects to a Clojure socket server, then sends over code
    that a) starts a custom REPL on top of the default REPL and b) starts a
    backchannel socket server. The `Client` then connects to the backchannel
    socket server and uses that connection to communicate with the Clojure
    runtime.

    Tutkain uses the REPL for evaluations and the backchannel for everything
    else (auto-completion, metadata lookup, static analysis, etc.)"""

    def start_workers(self):
        self.executor.submit(self.send_loop)
        self.executor.submit(self.recv_loop)
        return self

    def write_line(self, line):
        self.buffer.write(line)
        self.buffer.write("\n")
        self.buffer.flush()

    def module_loaded(self, response):
        if response.get(edn.Keyword("result")) == edn.Keyword("ok"):
            self.capabilities.add(response.get(edn.Keyword("filename")))

    def load_modules(self, modules):
        for filename, requires in modules.items():
            path = os.path.join(self.source_root, filename)

            with open(path, "rb") as file:
                self.backchannel.send({
                    "op": edn.Keyword("load-base64"),
                    "path": path,
                    "filename": filename,
                    "blob": base64.encode(file.read()),
                    "requires": requires
                }, self.module_loaded)

    @abstractmethod
    def handshake(self):
        pass

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.buffer = self.socket.makefile(mode="rw")
        log.debug({"event": "client/connect", "host": self.host, "port": self.port})

        log.debug({
            "event": "client/handshake",
            "data": self.executor.submit(lambda: read_until_prompt(self.socket)).result(timeout=5)
        })

        return self

    def source_path(self, filename):
        return posixpath.join(pathlib.Path(self.source_root).as_posix(), filename)

    def __init__(self, source_root, host, port, name, backchannel_opts={}):
        self.source_root = source_root
        self.host = host
        self.port = port
        self.name = name
        self.sendq = queue.Queue()
        self.printq = queue.Queue()
        self.handlers = {}
        self.executor = ThreadPoolExecutor(thread_name_prefix=f"{self.name}")
        self.namespace = "user"
        self.backchannel = types.SimpleNamespace(send=lambda *args, **kwargs: None, halt=lambda *args: None)
        self.backchannel_opts = backchannel_opts
        self.capabilities = set()

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

        form = item.get(edn.Keyword("form"))

        if (form := item.get(edn.Keyword("form"))) and (handler := self.handlers.get(form)):
            try:
                handler.__call__(item)
            finally:
                self.handlers.pop(form, None)
        else:
            self.printq.put(item)

    def recv_loop(self):
        try:
            while item := edn.read_line(self.buffer):
                log.debug({"event": "client/recv", "item": item})
                self.handle(item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            self.printq.put(edn.kwmap({
                "tag": edn.Keyword("ret"),
                "val": ":tutkain/disconnected"
            }))

            # Put a None into the queue to tell consumers to stop reading it.
            self.printq.put(None)

            # Feed poison pill to input queue.
            self.sendq.put(None)

            log.debug({"event": "thread/exit"})

            # We've exited the loop that reads from the socket, so we can
            # close the connection to the socket.
            if self.socket is not None:
                try:
                    self.buffer.close()
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                    log.debug({"event": "client/disconnect"})
                except OSError as error:
                    log.debug({"event": "error", "exception": error})

    def halt(self):
        log.debug({"event": "client/halt"})
        self.sendq.put(":repl/quit")
        self.executor.shutdown(wait=False)
        self.backchannel.halt()


class JVMClient(Client):
    def handshake(self):
        self.write_line("(ns tutkain.bootstrap)")
        self.buffer.readline()
        self.write_line("(def load-base64 (let [decoder (java.util.Base64/getDecoder)] (fn [blob file filename] (with-open [reader (-> decoder (.decode blob) (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader file filename)))))")
        self.buffer.readline()

        for filename in ["format.clj", "backchannel.clj", "repl.clj"]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.encode(file.read())
                self.write_line(f"""(load-base64 "{blob}" "{path}" "{os.path.basename(path)}")""")

            self.buffer.readline()

        backchannel_port = self.backchannel_opts.get("port", 0)
        backchannel_bind_address = self.backchannel_opts.get("bind_address", "localhost")
        self.write_line(f"""(try (tutkain.repl/repl {{:port {backchannel_port} :bind-address "{backchannel_bind_address}"}}) (catch Exception ex {{:tag :err :val (.toString ex)}}))""")
        line = self.buffer.readline()

        if not line.startswith('{'):
            self.printq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "Couldn't connect to Clojure REPL."
            }))

            self.printq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": line
            }))

            self.printq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "NOTE: Tutkain requires Clojure 1.10.0 or newer."
            }))
        else:
            ret = edn.read(line)

            if (host := ret.get(edn.Keyword("host"))):
                port = ret.get(edn.Keyword("port"))
                self.backchannel = backchannel.Client(self.printq.put).connect(host, port)
            elif (val := edn.read(ret.get(edn.Keyword("val")))) and isinstance(val, dict):
                host = val.get(edn.Keyword("host"))
                port = val.get(edn.Keyword("port"))
                self.backchannel = backchannel.Client(self.printq.put).connect(host, port)
            else:
                self.printq.put(ret)

        self.load_modules({
            "lookup.clj": [],
            "completions.clj": [],
            "load_blob.clj": [],
            "test.clj": [],
            "query.clj": [],
            "analyzer.clj": [
                edn.Symbol("clojure.tools.reader"),
                edn.Symbol("clojure.tools.analyzer.jvm")
            ]
        })

        self.write_line("""(println "Clojure" (clojure-version))""")
        self.printq.put(edn.read_line(self.buffer))

        log.debug({"event": "client/handshake", "data": self.buffer.readline()})
        self.start_workers()

    def __init__(self, source_root, host, port, backchannel_opts={}):
        super().__init__(source_root, host, port, "tutkain.clojure.client", backchannel_opts=backchannel_opts)

    def connect(self):
        super().connect()
        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line('(clojure.main/repl :prompt (constantly "") :need-prompt (constantly false))')
        self.handshake()
        return self

    def switch_namespace(self, ns):
        code = f"(do (or (some->> '{ns} find-ns ns-name in-ns) (ns {ns})) (set! *3 *2) (set! *2 *1))"
        self.handlers[code] = lambda _: None
        self.sendq.put(code)

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.printq.put

        self.backchannel.send({
            "op": edn.Keyword("set-eval-context"),
            "file": file,
            "line": line + 1,
            "column": column + 1
        }, lambda _: self.sendq.put(code))


class JSClient(Client):
    def __init__(self, source_root, host, port, prompt_for_build_id):
        super().__init__(source_root, host, port, "tutkain.cljs.client")
        self.prompt_for_build_id = prompt_for_build_id

    def connect(self):
        super().connect()
        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line('(clojure.main/repl :prompt (constantly "") :need-prompt (constantly false))')
        self.write_line("""(sort (shadow.cljs.devtools.api/get-build-ids))""")
        build_id_options = edn.read_line(self.buffer)

        self.executor.submit(
            self.prompt_for_build_id,
            build_id_options,
            lambda index: self.handshake(build_id_options[index])
        )

        return self

    def handshake(self, build_id):
        self.write_line("(ns tutkain.bootstrap)")
        self.buffer.readline()
        self.write_line("(def load-base64 (let [decoder (java.util.Base64/getDecoder)] (fn [blob file filename] (with-open [reader (-> decoder (.decode blob) (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader file filename)))))")
        self.buffer.readline()

        for filename in ["format.clj", "backchannel.clj", "shadow.clj"]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.encode(file.read())
                self.write_line(f"""(load-base64 "{blob}" "{path}" "{os.path.basename(path)}")""")

            self.buffer.readline()

        backchannel_port = self.backchannel_opts.get("port", 0)
        self.write_line(f"""(try (tutkain.shadow/repl {{:build-id {build_id} :port {backchannel_port}}}) (catch Exception ex {{:tag :err :val (.toString ex)}}))""")

        line = self.buffer.readline()
        val = edn.read(line)
        host = val.get(edn.Keyword("host"))
        port = val.get(edn.Keyword("port"))
        self.backchannel = backchannel.Client(self.printq.put).connect(host, port)

        self.load_modules({
            "lookup.clj": [],
            "completions.clj": [],
            "cljs.clj": [],
            "shadow.clj": [],
        })

        self.write_line("""(println "ClojureScript" *clojurescript-version*)""")
        line = self.buffer.readline()

        if not line.startswith('{'):
            self.printq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "Couldn't connect to ClojureScript REPL. Here's why:"
            }))

            self.printq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": line
            }))

            self.printq.put(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "Is the shadow-cljs watch running for the build ID you chose?"
            }))
        else:
            ret = edn.read(line)
            self.handle(ret)

            if ret.get(edn.Keyword("tag")) != edn.Keyword("err"):
                self.handle(edn.read_line(self.buffer))
                log.debug({"event": "client/handshake", "data": self.buffer.readline()})

        self.start_workers()

    def switch_namespace(self, ns):
        code = f"(in-ns '{ns})"
        self.handlers[code] = lambda _: None
        self.sendq.put(code)

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.printq.put
        self.sendq.put(code)


class BabashkaClient(Client):
    def __init__(self, source_root, host, port):
        super().__init__(source_root, host, port, "tutkain.bb.client")

    def handshake(self):
        self.write_line("""((requiring-resolve 'clojure.core.server/io-prepl))""")
        self.write_line("""(println "Babashka" (System/getProperty "babashka.version"))""")

        self.printq.put(edn.read_line(self.buffer))

        self.buffer.readline()
        self.start_workers()

    def connect(self):
        super().connect()
        self.handshake()
        return self

    def switch_namespace(self, ns):
        code = f"(in-ns '{ns})"
        self.handlers[code] = lambda _: None
        self.sendq.put(code)

    def eval(self, code, file="NO_SOURCE_FILE", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.printq.put
        self.sendq.put(code)
