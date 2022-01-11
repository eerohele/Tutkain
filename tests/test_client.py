from unittest import TestCase

from Tutkain.api import edn
from Tutkain.package import start_logging, stop_logging
from Tutkain.src import repl

from .mock import REPL, Backchannel


class TestJVMClient(TestCase):
    @classmethod
    def setUpClass(self):
        start_logging(False)

    @classmethod
    def tearDownClass(self):
        stop_logging()

    def test_smoke(self):
        def write_greeting(buf):
            buf.write("user=> ")
            buf.flush()

        with REPL(greeting=write_greeting) as server:
            client = repl.JVMClient(server.host, server.port)

            server.executor.submit(client.connect)
            # Client starts clojure.main/repl
            server.recv()

            # Client switches into the bootstrap namespace
            server.recv()
            server.send("nil\n")

            # Client defines load-base64 function
            server.recv()
            server.send("#'tutkain.bootstrap/load-base64\n")

            # Client loads modules
            server.recv()
            server.send("""#object[clojure.lang.MultiFn 0x7fb5c837 "clojure.lang.MultiFn@7fb5c837"]""")
            server.recv()
            server.send("#'tutkain.format/pp-str")
            server.recv()
            server.send("#'tutkain.backchannel/open")
            server.recv()
            server.send("#'tutkain.repl/repl")
            server.recv()

            with Backchannel() as backchannel:
                server.send(f"""{{:greeting "Clojure 1.11.0-alpha1\\n" :host "localhost", :port {backchannel.port}}}""")
                filenames = {"java.clj", "lookup.clj", "completions.clj", "load_blob.clj", "test.clj", "query.clj", "analyzer.clj", "analyzer/jvm.clj"}

                for filename in filenames:
                    response = edn.read(backchannel.recv())
                    self.assertEquals(edn.Keyword("load-base64"), response.get(edn.Keyword("op")))
                    self.assertTrue(response.get(edn.Keyword("filename")) in filenames)

                self.assertEquals({
                    "target": "view",
                    "val": "Clojure 1.11.0-alpha1\n"
                }, client.printq.get(timeout=1))

                client.evaluate("(inc 1)")

                response = edn.read(backchannel.recv())
                id = response.get(edn.Keyword("id"))

                self.assertEquals(
                    edn.kwmap({
                        "op": edn.Keyword("set-eval-context"),
                        "id": id,
                        "file": "NO_SOURCE_FILE",
                        "line": 1,
                        "column": 1
                    }),
                    response
                )

                backchannel.send(edn.kwmap({
                    "id": id,
                    "file": None,
                    "ns": edn.Symbol("user"),
                    "dialect": edn.Keyword("clj")
                }))

                self.assertEquals("(inc 1)\n", server.recv())
                server.send("2")
                self.assertEquals({
                    "target": "view",
                    "val": "2\n"
                }, client.printq.get(timeout=1))

            client.halt()
            self.assertEquals(":repl/quit", server.recv())
