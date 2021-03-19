from Tutkain.api import edn
from Tutkain.package import source_root, start_logging, stop_logging
from Tutkain.src.repl.client import Client
from Tutkain.src import state

from .mock import Server
from .util import ViewTestCase


def conduct_handshake(server):
    server.recv()

    with Server() as backchannel:
        server.send({
            edn.Keyword("tag"): edn.Keyword("ret"),
            edn.Keyword("val"): f"""{{:host "localhost", :port {backchannel.port}}}""",
        })

        form = server.recv()

        server.send({
            edn.Keyword("tag"): edn.Keyword("ret"),
            edn.Keyword("val"): "nil",
            edn.Keyword("ns"): "user",
            edn.Keyword("ms"): 253,
            edn.Keyword("form"): form
        })

        server.recv()

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

        return backchannel


class TestEvaluation(ViewTestCase):
    @classmethod
    def setUpClass(self):
        super(TestEvaluation, self).setUpClass()
        start_logging(False)

        self.server = Server(greeting="user=> ").start()
        self.client = Client(source_root(), self.server.host, self.server.port, wait=False).connect()
        state.set_view_client(self.view, self.client)
        state.set_repl_view(self.view)
        self.backchannel = conduct_handshake(self.server)

    @classmethod
    def tearDownClass(self):
        super(TestEvaluation, self).tearDownClass()
        stop_logging()

        if self.server:
            self.server.stop()

        if self.client:
            self.client.halt()

    def test_outermost(self):
        self.set_view_content("(comment (inc 1) (inc 2))")
        self.set_selections((9, 9), (17, 17))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.assertEquals("(inc 2)\n", self.server.recv())

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals("(range 10)\n", self.server.recv())

    def test_form(self):
        self.set_view_content("42 84")
        self.set_selections((0, 0), (3, 3))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.assertEquals("42\n", self.server.recv())
        self.assertEquals("84\n", self.server.recv())

    def test_parameterized(self):
        self.set_view_content("{:a 1} {:b 2}")
        self.set_selections((0, 0), (7, 7))
        self.view.run_command("tutkain_evaluate", {"code": "((requiring-resolve 'clojure.data/diff) $0 $1)"})
        self.assertEquals("((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})\n", self.server.recv())

    def test_ns(self):
        self.set_view_content("(ns foo.bar) (ns baz.quux) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "ns"})
        self.assertEquals("(ns foo.bar)\n", self.server.recv())
        self.assertEquals("(ns baz.quux)\n", self.server.recv())

    def test_view(self):
        self.set_view_content("(ns foo.bar) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        self.assertEquals(
            '{:op :load :code "(ns foo.bar) (defn x [y] y)" :file nil :dialect :clj :id 1}\n',
            self.backchannel.recv()
        )
