import io
import queue
import socket
from abc import ABC, abstractmethod
from concurrent import futures

from Tutkain.api import edn


class Server(ABC):
    def __init__(self, port=0, timeout=5):
        self.executor = futures.ThreadPoolExecutor()
        self.timeout = timeout
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(("localhost", port))
        self.socket.listen()
        self.socket.settimeout(self.timeout)
        self.host, self.port = self.socket.getsockname()
        self.recvq = queue.Queue()

    def recv(self, timeout=1):
        return self.recvq.get(timeout)

    def recv_loop(self):
        while message := self.buffer.readline():
            self.recvq.put(message)

    @abstractmethod
    def send(self, message):
        pass

    def handshake(self):
        pass

    def write_greeting(self):
        pass

    def accept(self):
        self.conn, address = self.socket.accept()
        self.conn.settimeout(self.timeout)
        self.buffer = self.conn.makefile(mode="rw", buffering=io.DEFAULT_BUFFER_SIZE)
        self.write_greeting()
        self.receiver = self.executor.submit(self.recv_loop)
        self.handshake()
        return self

    def start(self):
        self.connection = self.executor.submit(self.accept)
        return self

    def stop(self):
        self.socket.close()
        self.executor.shutdown(wait=False)


class PlainServer(Server):
    def send(self, message):
        self.buffer.write(message + "\n")
        self.buffer.flush()


class JvmServer(PlainServer):
    def write_greeting(self):
        self.buffer.write("user=> ")
        self.buffer.flush()


class JvmBackchannelServer(JvmServer):
    def handshake(self):
        # Client starts clojure.main/repl
        self.recv()

        # Client switches into the bootstrap namespace
        self.recv()
        self.send("nil")

        # Client defines load-base64 function
        self.recv()
        self.send("#'tutkain.bootstrap/load-base64")

        # Client loads modules
        self.recv()
        self.send("#'tutkain.format/pp-str")
        self.recv()
        self.send("#'tutkain.backchannel/open")
        self.recv()
        self.send(
            """#object[clojure.lang.MultiFn 0x7fb5c837 "clojure.lang.MultiFn@7fb5c837"]"""
        )
        self.recv()
        self.send("#'tutkain.repl/repl")

        # Client starts REPL
        self.recv()

        backchannel = Backchannel().start()
        self.send(f"""{{:host "localhost", :port {backchannel.port}}}""")
        # Client connects to backchannel
        self.backchannel = backchannel.connection.result(timeout=5)
        backchannel.send(
            edn.kwmap({"tag": edn.Keyword("out"), "val": "Clojure 1.11.0-alpha1\n"})
        )

        # Client loads modules
        for _ in range(9):
            module = edn.read(backchannel.recv())

            backchannel.send(
                edn.kwmap(
                    {
                        "id": module.get(edn.Keyword("id")),
                        "result": edn.Keyword("ok"),
                        "filename": module.get(edn.Keyword("filename")),
                    }
                )
            )

        return self.backchannel


class JvmRpcServer(JvmServer):
    def send(self, message):
        edn.write_line(self.buffer, message)

    def handshake(self):
        # Client starts clojure.main/repl
        self.recv()

        # Client switches into the bootstrap namespace
        self.recv()
        self.send("nil")

        # Client defines load-base64 function
        self.recv()
        self.send("#'tutkain.bootstrap/load-base64")

        # Client loads modules
        self.recv()
        self.send("#'tutkain.format/pp-str")
        self.recv()
        self.send("#'tutkain.backchannel/open")
        self.recv()
        self.send(
            """#object[clojure.lang.MultiFn 0x7fb5c837 "clojure.lang.MultiFn@7fb5c837"]"""
        )
        self.recv()
        self.send("#'tutkain.repl/repl")

        self.recv()

        # Client connects to backchannel
        self.send(
            edn.kwmap({"tag": edn.Keyword("out"), "val": "Clojure 1.11.0-alpha1\n"})
        )

        # Client loads modules
        for _ in range(9):
            module = edn.read(self.recv())

            self.send(
                edn.kwmap(
                    {
                        "id": module.get(edn.Keyword("id")),
                        "result": edn.Keyword("ok"),
                        "filename": module.get(edn.Keyword("filename")),
                    }
                )
            )

        return self


# TODO: Rename to RPC
class Backchannel(Server):
    def send(self, message):
        edn.write_line(self.buffer, message)


class JsServer(Backchannel):
    def write_greeting(self):
        self.buffer.write("shadow-cljs - REPL - see (help)\n")
        self.buffer.flush()
        self.buffer.write("To quit, type: :repl/quit\n")
        self.buffer.flush()
        self.buffer.write("shadow.user=> ")
        self.buffer.flush()

    def handshake(self):
        # Client starts clojure.main/repl
        self.recv()

        # Client requests build IDs
        self.recv()

        # Server sends build ID list
        self.send("[:browser, :node-script, :npm]")

        # Client switches into the bootstrap namespace
        self.recv()
        self.send("nil\n")

        # Client defines load-base64 function
        self.recv()
        self.send("#'tutkain.bootstrap/load-base64\n")

        # Client loads modules
        self.recv()
        self.send("#'tutkain.format/pp-str")
        self.recv()
        self.send("#'tutkain.backchannel/open")
        self.recv()
        self.send(
            """#object[clojure.lang.MultiFn 0x7fb5c837 "clojure.lang.MultiFn@7fb5c837"]"""
        )
        self.recv()
        self.send("#'tutkain.shadow/rpc")

        # Client starts REPL
        self.recv()

        self.send(
            edn.kwmap({"tag": edn.Keyword("out"), "val": "ClojureScript 1.10.844\n"})
        )

        for _ in range(8):
            module = edn.read(self.recv())

            self.send(
                edn.kwmap(
                    {
                        "id": module.get(edn.Keyword("id")),
                        "result": edn.Keyword("ok"),
                        "filename": module.get(edn.Keyword("filename")),
                    }
                )
            )

        # TODO: Add test for no runtime

        return self


class BabashkaServer(PlainServer):
    def write_greeting(self):
        self.buffer.write("Babashka v0.3.6 REPL.\n")
        self.buffer.flush()
        self.buffer.write("Use :repl/quit or :repl/exit to quit the REPL.\n")
        self.buffer.flush()
        self.buffer.write("Clojure rocks, Bash reaches.\n")
        self.buffer.flush()
        self.buffer.write("\n")
        self.buffer.flush()
        self.buffer.write("user=> ")
        self.buffer.flush()

    def handshake(self):
        # Client starts clojure.main/repl
        self.recv()

        # Client switches into the bootstrap namespace
        self.recv()
        self.send("nil")

        # Client defines load-base64 function
        self.recv()
        self.send("#'tutkain.bootstrap/load-base64")

        # Client loads modules
        self.recv()
        self.send("#'tutkain.format/pp-str")
        self.recv()
        self.send("#'tutkain.backchannel/open")
        self.recv()
        self.send(
            """#object[clojure.lang.MultiFn 0x7fb5c837 "clojure.lang.MultiFn@7fb5c837"]"""
        )
        self.recv()
        self.send("#'tutkain.repl/repl")

        # Client starts REPL
        self.recv()

        backchannel = Backchannel().start()
        self.send(f"""{{:host "localhost", :port {backchannel.port}}}""")
        # Client connects to backchannel
        self.backchannel = backchannel.connection.result(timeout=1)
        backchannel.send(
            edn.kwmap({"tag": edn.Keyword("out"), "val": "Clojure 1.11.1-SCI\n"})
        )

        # Client loads modules
        for _ in range(6):
            module = edn.read(backchannel.recv())

            backchannel.send(
                edn.kwmap(
                    {
                        "id": module.get(edn.Keyword("id")),
                        "result": edn.Keyword("ok"),
                        "filename": module.get(edn.Keyword("filename")),
                    }
                )
            )

        return self.backchannel
