from unittest import TestCase

from Tutkain.api import edn
from Tutkain.package import source_root, start_logging, stop_logging
from Tutkain.src.repl.client import Client

from .mock import Server


class TestClient(TestCase):
    @classmethod
    def setUpClass(self):
        start_logging(False)

    @classmethod
    def tearDownClass(self):
        stop_logging()

    def test_smoke(self):
        with Server(greeting="user=> ") as server:
            with Client(source_root(), server.host, server.port, wait=False) as client:
                # Client starts sub-REPL
                server.recv()

                with Server() as backchannel:
                    server.send({
                        edn.Keyword("tag"): edn.Keyword("ret"),
                        edn.Keyword("val"): f"""{{:host "localhost", :port {backchannel.port}}}""",
                    })

                    # Client sends load-file request for backchannel assets
                    form = server.recv()

                    # Server ack
                    server.send({
                        edn.Keyword("tag"): edn.Keyword("ret"),
                        edn.Keyword("val"): "nil",  # really nil\n
                        edn.Keyword("ns"): "user",
                        edn.Keyword("ms"): 253,
                        edn.Keyword("form"): form
                    })

                    self.assertEquals(
                        Client.handshake_payloads["print_version"],
                        server.recv().rstrip()
                    )

                    server.send({
                        edn.Keyword("tag"): edn.Keyword("out"),
                        edn.Keyword("val"): "Clojure 1.11.0-alpha1"
                    })

                    server.send({
                        edn.Keyword("tag"): edn.Keyword("ret"),
                        edn.Keyword("val"): "nil",
                        edn.Keyword("ns"): "user",
                        edn.Keyword("ms"): 0,
                        edn.Keyword("form"): Client.handshake_payloads["print_version"]
                    })

                    self.assertEquals({
                        "printable": "Clojure 1.11.0-alpha1\n",
                        "response": {
                            edn.Keyword("tag"): edn.Keyword("out"),
                            edn.Keyword("val"): "Clojure 1.11.0-alpha1"
                        }
                    }, client.printq.get(timeout=1))

                    client.eval("(inc 1)")
                    self.assertEquals("(inc 1)\n", server.recv())

                    response = {
                        edn.Keyword("tag"): edn.Keyword("ret"),
                        edn.Keyword("val"): "2",
                        edn.Keyword("ns"): "user",
                        edn.Keyword("ms"): 1,
                        edn.Keyword("form"): "(inc 1)"
                    }

                    server.send(response)

                    self.assertEquals(
                        {"printable": "2\n", "response": response},
                        client.printq.get(timeout=1)
                    )

        self.assertEquals(":repl/quit\n", server.recv())
