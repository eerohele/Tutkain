from Tutkain.api import edn
from Tutkain.package import source_root, start_logging, stop_logging
from Tutkain.src.repl import views
from Tutkain.src.repl.client import JVMClient, JSClient
from Tutkain.src import state

from .mock import Server
from .util import ViewTestCase


class TestJVMClient(ViewTestCase):
    @classmethod
    def conduct_handshake(self):
        server = self.server

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
        server.send("#'tutkain.format/pp-str")
        server.recv()
        server.send("#'tutkain.backchannel/open")
        server.recv()
        server.send("#'tutkain.repl/repl")
        server.recv()

        with Server() as backchannel:
            server.send({
                edn.Keyword("tag"): edn.Keyword("ret"),
                edn.Keyword("val"): f"""{{:host "localhost", :port {backchannel.port}}}""",
            })

            for _ in range(4):
                backchannel.recv()

            server.send({
                edn.Keyword("tag"): edn.Keyword("out"),
                edn.Keyword("val"): "Clojure 1.11.0-alpha1"
            })

            server.send({
                edn.Keyword("tag"): edn.Keyword("ret"),
                edn.Keyword("val"): "nil",
                edn.Keyword("ns"): "user",
                edn.Keyword("ms"): 0,
                edn.Keyword("form"): JVMClient.handshake_payloads["print_version"]
            })

            server.recv()

            return backchannel

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        start_logging(False)

        def write_greeting(buf):
            buf.write("user=> ")
            buf.flush()

        self.server = Server(greeting=write_greeting).start()
        self.client = JVMClient(source_root(), self.server.host, self.server.port, wait=False).connect()
        dialect = edn.Keyword("clj")
        state.set_view_client(self.view, dialect, self.client)
        repl_view = views.configure(self.view.window(), self.client, dialect)
        state.set_repl_view(repl_view, dialect)
        self.backchannel = self.conduct_handshake()

    @classmethod
    def tearDownClass(self):
        super(TestJVMClient, self).tearDownClass()
        stop_logging()

        if self.server:
            self.server.stop()

        if self.client:
            self.client.halt()

    def eval_context(self, ns="user", file="NO_SOURCE_FILE", line=1, column=1):
        actual = edn.read(self.backchannel.recv())
        id = actual.get(edn.Keyword("id"))

        response = edn.kwmap({
             "id": id,
             "op": edn.Keyword("set-eval-context"),
             "file": file,
             "line": line,
             "column": column,
        })

        self.assertEquals(response, actual)

        self.backchannel.send(edn.kwmap({
            "id": id,
            "file": file,
            "ns": edn.Symbol(ns)
        }))

    def test_outermost(self):
        self.set_view_content("(comment (inc 1) (inc 2))")
        self.set_selections((9, 9), (17, 17))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})

        self.eval_context(column=10)
        self.eval_context(column=18)

        self.assertEquals("(inc 1)\n", self.server.recv())
        self.assertEquals("(inc 2)\n", self.server.recv())

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=10)
        self.assertEquals("(range 10)\n", self.server.recv())

    def test_form(self):
        self.set_view_content("42 84")
        self.set_selections((0, 0), (3, 3))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.eval_context()
        self.eval_context(column=4)
        self.assertEquals("42\n", self.server.recv())
        self.assertEquals("84\n", self.server.recv())

    def test_parameterized(self):
        self.set_view_content("{:a 1} {:b 2}")
        self.set_selections((0, 0), (7, 7))
        self.view.run_command("tutkain_evaluate", {"code": "((requiring-resolve 'clojure.data/diff) $0 $1)"})
        self.eval_context()
        self.assertEquals("((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})\n", self.server.recv())

    def test_eval_in_ns(self):
        self.view.run_command("tutkain_evaluate", {"code": "(reset)", "ns": "user"})
        self.eval_context()
        # Clients sends ns first
        self.assertTrue(self.server.recv().startswith("^:tutkain/internal"))
        self.eval_context()
        self.assertEquals("(reset)\n", self.server.recv())

    def test_ns(self):
        self.set_view_content("(ns foo.bar) (ns baz.quux) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "ns"})
        self.eval_context(ns="baz.quux")
        self.assertEquals("(ns foo.bar)\n", self.server.recv())
        self.eval_context(ns="baz.quux", column=14)
        self.assertEquals("(ns baz.quux)\n", self.server.recv())

    def test_view(self):
        self.set_view_content("(ns foo.bar) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        response = edn.read(self.backchannel.recv())

        self.assertEquals({
            edn.Keyword("op"): edn.Keyword("load"),
            edn.Keyword("code"): "(ns foo.bar) (defn x [y] y)",
            edn.Keyword("file"): None,
            edn.Keyword("dialect"): edn.Keyword("clj"),
            edn.Keyword("id"): response.get(edn.Keyword("id"))
        }, response)

    def test_discard(self):
        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=3)
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.eval_context(column=3)
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.set_view_content("(inc #_(dec 2) 4)")
        self.set_selections((14, 14))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=8)
        self.assertEquals("(dec 2)\n", self.server.recv())
        self.set_view_content("#_:a")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.eval_context(column=3)
        self.assertEquals(":a\n", self.server.recv())

    def test_lookup(self):
        self.set_view_content("(rand)")

        for n in range(1, 5):
            self.set_selections((n, n))

            self.view.run_command("tutkain_show_information", {
                "selector": "variable.function"
            })

            response = edn.read(self.backchannel.recv())

            self.assertEquals({
                edn.Keyword("op"): edn.Keyword("lookup"),
                edn.Keyword("named"): "rand",
                edn.Keyword("ns"): None,
                edn.Keyword("id"): response.get(edn.Keyword("id"))
            }, response)

    def test_lookup_head(self):
        self.set_view_content("(map inc )")
        self.set_selections((9, 9))

        self.view.run_command("tutkain_show_information", {
            "selector": "variable.function",
            "seek_backward": True
        })

        response = edn.read(self.backchannel.recv())

        self.assertEquals({
            edn.Keyword("op"): edn.Keyword("lookup"),
            edn.Keyword("named"): "map",
            edn.Keyword("ns"): None,
            edn.Keyword("id"): response.get(edn.Keyword("id"))
        }, response)


class TestJSClient(ViewTestCase):
    @classmethod
    def conduct_handshake(self):
        server = self.server

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
        server.send("#'tutkain.format/pp-str")
        server.recv()
        server.send("#'tutkain.backchannel/open")
        server.recv()
        server.send("#'tutkain.repl/repl")

        # Client starts REPL
        server.recv()

        # Server sends build ID list
        server.send([
            edn.Keyword("browser"),
            edn.Keyword("node-script"),
            edn.Keyword("npm")
        ])

        # Client responds with build ID
        server.recv()

        with Server() as backchannel:
            server.send({
                edn.Keyword("host"): "localhost",
                edn.Keyword("port"): backchannel.port
            })

            for _ in range(4):
                backchannel.recv()

            # Client sends version print
            server.recv()

            server.send({
                edn.Keyword("tag"): edn.Keyword("out"),
                edn.Keyword("val"): "ClojureScript 1.10.844"
            })

            server.send({
                edn.Keyword("tag"): edn.Keyword("out"),
                edn.Keyword("val"): "\\n"
            })

            server.send({
                edn.Keyword("tag"): edn.Keyword("ret"),
                edn.Keyword("val"): "nil",
                edn.Keyword("ns"): "cljs.user",
                edn.Keyword("ms"): 0,
                edn.Keyword("form"): """(println "ClojureScript" *clojurescript-version*)"""
            })

            # TODO: Add test for no runtime

            return backchannel

    @classmethod
    def prompt_for_build_id(self, _, f):
        return f(edn.Keyword("node-script"))

    @classmethod
    def setUpClass(self):
        super().setUpClass(syntax="ClojureScript (Tutkain).sublime-syntax")
        start_logging(False)

        def write_greeting(buf):
            buf.write("shadow-cljs - REPL - see (help)\n")
            buf.flush()
            buf.write("To quit, type: :repl/quit\n")
            buf.flush()
            buf.write("shadow.user=> ")
            buf.flush()

        self.server = Server(greeting=write_greeting)

        self.server.start()

        self.client = JSClient(
            source_root(),
            self.server.host,
            self.server.port,
            self.prompt_for_build_id
        ).connect()

        dialect = edn.Keyword("cljs")
        state.set_view_client(self.view, dialect, self.client)
        repl_view = views.configure(self.view.window(), self.client, dialect)
        state.set_repl_view(repl_view, dialect)
        self.backchannel = self.conduct_handshake()

    @classmethod
    def tearDownClass(self):
        super(TestJSClient, self).tearDownClass()
        stop_logging()

        if self.server:
            self.server.stop()

        if self.client:
            self.client.halt()

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals("(range 10)\n", self.server.recv())
