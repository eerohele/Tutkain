from concurrent.futures import ThreadPoolExecutor
from inspect import cleandoc
import base64
import queue
import os
import select
import socket

from .backchannel import Backchannel, NoopBackchannel
from ...api import edn
from ..log import log


class Client(object):
    handshake_payloads = {
        "print_version": """#?(:bb (println "Babashka" (System/getProperty "babashka.version")) :clj (println "Clojure" (clojure-version)))"""
    }

    def start_workers(self, _):
        self.executor.submit(self.send_loop)
        self.executor.submit(self.recv_loop)
        self.executor.submit(self.format_loop)
        return self

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

    def load_modules(self, backchannel):
        for filename, requires in [
            ("lookup.clj", []),
            ("completions.clj", []),
            ("load_blob.clj", []),
            ("test.clj", []),
            ("cljs.clj", [edn.Symbol("cljs.core")])
        ]:
            path = os.path.join(self.source_root, filename)

            with open(path, "rb") as file:
                backchannel.send({
                    edn.Keyword("op"): edn.Keyword("load-base64"),
                    edn.Keyword("path"): path,
                    edn.Keyword("filename"): filename,
                    edn.Keyword("blob"): base64.b64encode(file.read()).decode("utf-8"),
                    edn.Keyword("requires"): requires
                })

    def handshake(self):
        log.debug({"event": "client/handshake", "data": self.sink_all()})
        path = os.path.join(self.source_root, "repl.clj")

        with open(path, "rb") as file:
            blob = base64.b64encode(file.read()).decode("utf-8")
            backchannel_port = self.backchannel_opts.get("port", 0)
            self.write_line(f"""#?(:bb (do (prn {{:tag :ret :val "{{}}"}}) ((requiring-resolve 'clojure.core.server/io-prepl))) :clj (do (with-open [reader (-> (java.util.Base64/getDecoder) (.decode "{blob}") (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader "{os.path.abspath(path)}" "{os.path.basename(path)}")) (try (tutkain.repl/repl {{:port {backchannel_port}}}) (catch Exception ex {{:tag :err :val (.toString ex)}}))))""")

        ret = edn.read_line(self.buffer)

        if isinstance(ret, dict) and (host := ret.get(edn.Keyword("host"))):
            port = ret.get(edn.Keyword("port"))
            self.backchannel = Backchannel(host, port).connect()
            self.bare = True
        elif isinstance(ret, dict) and (val := edn.read(ret.get(edn.Keyword("val")))) and isinstance(val, dict):
            host = val.get(edn.Keyword("host"))
            port = val.get(edn.Keyword("port"))
            self.backchannel = Backchannel(host, port).connect()
        else:
            self.recvq.put(ret)

        self.load_modules(self.backchannel)
        self.write_line(self.handshake_payloads["print_version"])

        if self.bare:
            self.recvq.put({edn.Keyword("out"): self.buffer.readline()})
        else:
            self.recvq.put(edn.read_line(self.buffer))

        log.debug({"event": "client/handshake", "data": self.buffer.readline()})

        return True

    def connect(self, then=lambda _: None):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.buffer = self.socket.makefile(mode="rw")

        log.debug({"event": "client/connect", "host": self.host, "port": self.port})
        handshake = self.executor.submit(self.handshake)
        handshake.add_done_callback(self.start_workers)
        handshake.add_done_callback(then)

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

    def __init__(self, source_root, host, port, backchannel_opts={}, wait=5):
        self.source_root = source_root
        self.host = host
        self.port = port
        self.sendq = queue.Queue()
        self.recvq = queue.Queue()
        self.printq = queue.Queue()
        self.backchannel = NoopBackchannel()
        self.handlers = {}
        self.namespace = "user"
        self.bare = False
        self.backchannel_opts = backchannel_opts
        self.wait = wait

        self.executor = ThreadPoolExecutor(thread_name_prefix="tutkain.client")

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

    def eval(self, code, dialect=edn.Keyword("clj"), file="NO_SOURCE_FILE", ns="user", line=0, column=0, handler=None):
        self.handlers[code] = handler or self.recvq.put

        self.backchannel.send({
            edn.Keyword("op"): edn.Keyword("set-eval-context"),
            edn.Keyword("dialect"): dialect,
            edn.Keyword("file"): file,
            edn.Keyword("ns"): edn.Symbol(ns),
            edn.Keyword("line"): line + 1,
            edn.Keyword("column"): column + 1
        }, lambda _: self.sendq.put(code))

    def read_line(self):
        if self.bare:
            return self.buffer.readline()
        else:
            return edn.read_line(self.buffer)

    def handle(self, item):
        if ns := item.get(edn.Keyword("ns")):
            self.namespace = ns

        if (form := item.get(edn.Keyword("form"))) and (handler := self.handlers.get(form)):
            handler.__call__(item)
        else:
            self.recvq.put(item)

    def recv_loop(self):
        try:
            while item := self.read_line():
                log.debug({"event": "client/recv", "item": item})
                self.handle(item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            self.recvq.put({
                edn.Keyword("tag"): edn.Keyword("ret"),
                edn.Keyword("val"): ":tutkain/disconnected"
            })

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

        if summary := response.get(edn.Keyword("summary")):
            return summary + "\n"

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
        self.backchannel.halt()
        self.recvq.put(None)
        self.sendq.put(":repl/quit")

    def __exit__(self, type, value, traceback):
        self.halt()
