import sublime
import queue
import unittest

from Tutkain.api import edn
from Tutkain.package import source_root, start_logging, stop_logging
from Tutkain.src.repl import views
from Tutkain.src.repl.client import BabashkaClient, JVMClient, JSClient
from Tutkain.src import base64
from Tutkain.src import state
from Tutkain.src import test

from .mock import Server


class PackageTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        sublime.run_command("new_window")
        self.window = sublime.active_window()

    @classmethod
    def tearDownClass(self):
        if self.window:
            self.window.run_command("close_window")

    def setUp(self, syntax="Clojure (Tutkain).sublime-syntax"):
        self.view = self.window.new_file()
        self.view.set_name("tutkain.clj")
        self.view.set_scratch(True)
        self.view.window().focus_view(self.view)
        self.view.assign_syntax(syntax)

    def tearDown(self):
        if self.view:
            self.view.close()

    def set_view_content(self, chars):
        self.view.run_command("select_all")
        self.view.run_command("right_delete")
        self.view.run_command("append", {"characters": chars})

    def set_selections(self, *pairs):
        self.view.sel().clear()

        for begin, end in pairs:
            self.view.sel().add(sublime.Region(begin, end))


class TestJVMClient(PackageTestCase):
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

            # Client loads modules
            for _ in range(5):
                module = edn.read(backchannel.recv())

                backchannel.send(edn.kwmap({
                    "id": module.get(edn.Keyword("id")),
                    "result": edn.Keyword("ok"),
                    "filename": module.get(edn.Keyword("filename"))
                }))

            server.send({
                edn.Keyword("tag"): edn.Keyword("out"),
                edn.Keyword("val"): "Clojure 1.11.0-alpha1"
            })

            server.send({
                edn.Keyword("tag"): edn.Keyword("ret"),
                edn.Keyword("val"): "nil",
                edn.Keyword("ns"): "user",
                edn.Keyword("ms"): 0,
                edn.Keyword("form"): """(println "Clojure" (clojure-version))"""
            })

            server.recv()

            # Clojure version info is printed on the client
            self.client.printq.get(timeout=5)

            return backchannel

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        start_logging(True)

        def write_greeting(buf):
            buf.write("user=> ")
            buf.flush()

        self.server = Server(greeting=write_greeting).start()
        self.client = JVMClient(source_root(), self.server.host, self.server.port)
        self.server.executor.submit(self.client.connect)
        dialect = edn.Keyword("clj")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, self.client)
        state.set_view_client(self.repl_view, dialect, self.client)
        state.set_repl_view(self.repl_view, dialect)
        self.backchannel = self.conduct_handshake()

    @classmethod
    def tearDownClass(self):
        super().tearDownClass()
        stop_logging()

        if self.repl_view:
            self.repl_view.close()

        if self.server:
            self.server.stop()

        if self.client:
            self.client.halt()

    def setUp(self):
        super().setUp()
        self.server.recvq = queue.Queue()
        self.backchannel.recvq = queue.Queue()

    def get_print(self):
        return self.client.printq.get(timeout=5)

    def print_item(self, ns, code):
        return {
            "printable": f"""{ns}=> {code}\n""",
            "response": {
                edn.Keyword("in"): f"""{code}"""
            }
        }

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
        self.assertEquals(self.print_item("user", "(inc 1)"), self.get_print())
        self.assertEquals("(inc 2)\n", self.server.recv())
        self.assertEquals(self.print_item("user", "(inc 2)"), self.get_print())

    def test_outermost_empty(self):
        self.set_view_content("")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.assertRaises(queue.Empty, lambda: self.server.recvq.get_nowait())

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=10)
        self.assertEquals("(range 10)\n", self.server.recv())
        self.assertEquals(self.print_item("user", "(range 10)"), self.get_print())

    def test_form(self):
        self.set_view_content("42 84")
        self.set_selections((0, 0), (3, 3))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.eval_context()
        self.assertEquals(self.print_item("user", "42"), self.get_print())
        self.eval_context(column=4)
        self.assertEquals(self.print_item("user", "84"), self.get_print())
        self.assertEquals("42\n", self.server.recv())
        self.assertEquals("84\n", self.server.recv())

    def test_parameterized(self):
        self.set_view_content("{:a 1} {:b 2}")
        self.set_selections((0, 0), (7, 7))
        self.view.run_command("tutkain_evaluate", {"code": "((requiring-resolve 'clojure.data/diff) $0 $1)"})
        self.eval_context()
        self.assertEquals("((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})\n", self.server.recv())
        self.assertEquals(
            self.print_item("user", "((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})"),
            self.get_print()
        )

    def test_eval_in_ns(self):
        self.view.run_command("tutkain_evaluate", {"code": "(reset)", "ns": "user"})
        self.eval_context()
        self.assertEquals(self.print_item("user", "(reset)"), self.get_print())
        # Clients sends ns first
        ret = self.server.recv()
        self.assertTrue(ret.startswith("(do (or (some->> "))
        self.assertEquals("(reset)\n", self.server.recv())

    def test_ns(self):
        self.set_view_content("(ns foo.bar) (ns baz.quux) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "ns"})
        self.eval_context(ns="baz.quux")
        self.assertEquals(self.print_item("user", "(ns foo.bar)"), self.get_print())
        self.assertEquals("(ns foo.bar)\n", self.server.recv())
        self.eval_context(ns="baz.quux", column=14)
        self.assertEquals(self.print_item("user", "(ns baz.quux)"), self.get_print())
        self.assertEquals("(ns baz.quux)\n", self.server.recv())

    def test_view(self):
        self.set_view_content("(ns foo.bar) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        response = edn.read(self.backchannel.recv())

        self.assertEquals({
            edn.Keyword("op"): edn.Keyword("load"),
            edn.Keyword("code"): base64.encode("(ns foo.bar) (defn x [y] y)".encode("utf-8")),
            edn.Keyword("file"): None,
            edn.Keyword("id"): response.get(edn.Keyword("id"))
        }, response)

    def test_view_common(self):
        self.view.assign_syntax("Packages/Tutkain/Clojure Common (Tutkain).sublime-syntax")
        self.set_view_content("(ns foo.bar) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        response = edn.read(self.backchannel.recv())

        self.assertEquals({
            edn.Keyword("op"): edn.Keyword("load"),
            edn.Keyword("code"): base64.encode("(ns foo.bar) (defn x [y] y)".encode("utf-8")),
            edn.Keyword("file"): None,
            edn.Keyword("id"): response.get(edn.Keyword("id"))
        }, response)

    def test_discard(self):
        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=3)
        self.assertEquals(self.print_item("user", "(inc 1)"), self.get_print())
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.eval_context(column=3)
        self.assertEquals(self.print_item("user", "(inc 1)"), self.get_print())
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.set_view_content("(inc #_(dec 2) 4)")
        self.set_selections((14, 14))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=8)
        self.assertEquals(self.print_item("user", "(dec 2)"), self.get_print())
        self.assertEquals("(dec 2)\n", self.server.recv())
        self.set_view_content("#_:a")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.eval_context(column=3)
        self.assertEquals(self.print_item("user", ":a"), self.get_print())
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
                edn.Keyword("dialect"): edn.Keyword("clj"),
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
            edn.Keyword("dialect"): edn.Keyword("clj"),
            edn.Keyword("id"): response.get(edn.Keyword("id"))
        }, response)

    def test_issue_46(self):
        code = """(apply str (repeat 9126 "x"))"""
        self.set_view_content(code)
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context()
        self.assertEquals(self.print_item("user", code), self.get_print())
        retval = "x" * 9126
        response = edn.kwmap({"tag": edn.Keyword("ret"), "val": retval})
        self.assertEquals(code + "\n", self.server.recv())
        self.server.send(response)
        self.assertEqual({
            "printable": retval,
            "response": response
        }, self.get_print())

    def test_evaluate_dialect(self):
        self.view.run_command("tutkain_evaluate", {"code": "(random-uuid)", "dialect": "cljs"})
        # The server receives no message because the evaluation uses a
        # different dialect than the server.
        self.assertRaises(queue.Empty, lambda: self.server.recvq.get_nowait())
        self.view.run_command("tutkain_evaluate", {"code": """(Integer/parseInt "42")""", "dialect": "clj"})
        self.eval_context()
        self.assertEquals("""(Integer/parseInt "42")\n""", self.server.recv())
        self.get_print()

    def test_async_run_tests_ns(self):
        code = """
        (ns my.app
          (:require [clojure.test :refer [deftest is]]))

        (deftest my-test
          (is (= 2 (+ 1 1))))
        """

        self.set_view_content(code)
        self.view.run_command("tutkain_run_tests", {"scope": "ns"})
        response = edn.read(self.backchannel.recv())
        id = response.get(edn.Keyword("id"))

        self.assertEquals(edn.kwmap({
            "op": edn.Keyword("test"),
            "file": None,
            "ns": "my.app",
            "vars": [],
            "code": base64.encode(code.encode("utf-8")),
            "id": id
        }), response)

        val = "{:test 1, :pass 1, :fail 0, :error 0, :assert 1, :type :summary}"

        self.backchannel.send(edn.kwmap({
            "id": id,
            "tag": edn.Keyword("ret"),
            "val": val,
            "pass": [edn.kwmap({
                        "type": edn.Keyword("pass"),
                        "line": 5,
                        "var-meta": edn.kwmap({
                            "line": 4,
                            "column": 1,
                            "file": "NO_SOURCE_FILE",
                            "name": edn.Symbol("my-test"),
                            "ns": "my.app"
                        })
                    })],
            "fail": [],
            "error": []
        }))

        self.assertEquals(val, self.get_print().get("printable"))
        self.assertEquals(
            [sublime.Region(78, 78)],
            test.regions(self.view, "passes")
        )

        self.assertFalse(test.regions(self.view, "fail"))
        self.assertFalse(test.regions(self.view, "error"))

    def test_async_unsuccessful_tests(self):
        code = """
        (ns my.app
          (:require [clojure.test :refer [deftest is]]))

        (deftest my-test
          (is (= 3 (+ 1 1))))
        """

        self.set_view_content(code)
        self.view.run_command("tutkain_run_tests", {"scope": "ns"})
        response = edn.read(self.backchannel.recv())
        id = response.get(edn.Keyword("id"))

        self.assertEquals(edn.kwmap({
            "op": edn.Keyword("test"),
            "file": None,
            "ns": "my.app",
            "vars": [],
            "code": base64.encode(code.encode("utf-8")),
            "id": id
        }), response)

        val = "{:test 1, :pass 0, :fail 1, :error 0, :assert 1, :type :summary}"

        self.backchannel.send(edn.kwmap({
            "id": id,
            "tag": edn.Keyword("ret"),
            "val": val,
            "pass": [],
            "fail": [edn.kwmap({
                        "file": None,
                        "type": edn.Keyword("fail"),
                        "line": 5,
                        "expected": "3\\n",
                        "actual": "2\\n",
                        "message": None,
                        "var-meta": edn.kwmap({
                            "line": 4,
                            "column": 1,
                            "file": "NO_SOURCE_FILE",
                            "name": edn.Symbol("my-test"),
                            "ns": "my.app"
                        })
                    })],
            "error": []
        }))

        self.assertEquals(val, self.get_print().get("printable"))
        self.assertEquals(
            [sublime.Region(78, 78)],
            test.regions(self.view, "failures")
        )

        self.assertEquals(
            [{"name": "my-test", "region": [78, 78], "type": "fail"}],
            test.unsuccessful(self.view)
        )

        self.assertFalse(test.regions(self.view, "passes"))
        self.assertFalse(test.regions(self.view, "error"))


class TestJSClient(PackageTestCase):
    @classmethod
    def conduct_handshake(self):
        server = self.server

        # Client starts clojure.main/repl
        server.recv()

        # Client requests build IDs
        server.recv()

        # Server sends build ID list
        server.send([
            edn.Keyword("browser"),
            edn.Keyword("node-script"),
            edn.Keyword("npm")
        ])

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
    def setUpClass(self):
        super().setUpClass()
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
            lambda _, on_done: on_done(1)
        )

        self.server.executor.submit(self.client.connect)

        dialect = edn.Keyword("cljs")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, self.client)
        state.set_view_client(self.repl_view, dialect, self.client)
        state.set_repl_view(self.repl_view, dialect)
        self.backchannel = self.conduct_handshake()

    @classmethod
    def tearDownClass(self):
        super().tearDownClass()
        stop_logging()

        if self.repl_view:
            self.repl_view.close()

        if self.server:
            self.server.stop()

        if self.client:
            self.client.halt()

    def setUp(self):
        super().setUp(syntax="ClojureScript (Tutkain).sublime-syntax")
        self.server.recvq = queue.Queue()
        self.backchannel.recvq = queue.Queue()

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals("(range 10)\n", self.server.recv())


class TestBabashkaClient(PackageTestCase):
    @classmethod
    def conduct_handshake(self):
        server = self.server

        # Client starts io-prepl
        server.recv()

        # Client sends version print
        server.recv()

        server.send({
            edn.Keyword("tag"): edn.Keyword("out"),
            edn.Keyword("val"): """Babashka 0.3.6""",
        })

        server.send({
            edn.Keyword("tag"): edn.Keyword("ret"),
            edn.Keyword("val"): "nil",
            edn.Keyword("ns"): "user",
            edn.Keyword("ms"): 0,
            edn.Keyword("form"): """(println "Babashka" (System/getProperty "babashka.version"))""",
        })

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        start_logging(False)

        def write_greeting(buf):
            buf.write("Babashka v0.3.6 REPL.\n")
            buf.flush()
            buf.write("Use :repl/quit or :repl/exit to quit the REPL.\n")
            buf.flush()
            buf.write("Clojure rocks, Bash reaches.\n")
            buf.flush()
            buf.write("\n")
            buf.flush()
            buf.write("user=> ")
            buf.flush()

        self.server = Server(greeting=write_greeting)

        self.server.start()

        self.client = BabashkaClient(
            source_root(),
            self.server.host,
            self.server.port
        )

        self.server.executor.submit(self.client.connect)
        dialect = edn.Keyword("bb")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, self.client)
        state.set_view_client(self.repl_view, dialect, self.client)
        state.set_repl_view(self.repl_view, dialect)
        self.conduct_handshake()

    # TODO: Extract into base class
    @classmethod
    def tearDownClass(self):
        super().tearDownClass()
        stop_logging()

        if self.repl_view:
            self.repl_view.close()

        if self.server:
            self.server.stop()

        if self.client:
            self.client.halt()

    def setUp(self):
        super().setUp(syntax="Babashka (Tutkain).sublime-syntax")
        self.server.recvq = queue.Queue()

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals("(range 10)\n", self.server.recv())
