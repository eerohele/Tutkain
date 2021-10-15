import io
import sublime
import queue
import unittest

from Tutkain.api import edn
from Tutkain.package import source_root, start_logging, stop_logging
from Tutkain.src import repl
from Tutkain.src.repl import views
from Tutkain.src import base64
from Tutkain.src import state
from Tutkain.src import test

from .mock import Server, send_edn, send_text


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
        server.send("nil")

        # Client defines load-base64 function
        server.recv()
        server.send("#'tutkain.bootstrap/load-base64")

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

        with Server(send_edn) as backchannel:
            server.send(f"""{{:greeting "Clojure 1.11.0-alpha1" :host "localhost", :port {backchannel.port}}}""")

            # Client loads modules
            for _ in range(7):
                module = edn.read(backchannel.recv())

                backchannel.send(edn.kwmap({
                    "id": module.get(edn.Keyword("id")),
                    "result": edn.Keyword("ok"),
                    "filename": module.get(edn.Keyword("filename"))
                }))

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

        self.server = Server(send_text, greeting=write_greeting).start()
        self.client = repl.JVMClient(source_root(), self.server.host, self.server.port)
        self.server.executor.submit(self.client.connect)
        dialect = edn.Keyword("clj")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, self.client.host, self.client.port)
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

    def eval_context(self, file="NO_SOURCE_FILE", line=1, column=1):
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
            "file": file
        }))

    def test_outermost(self):
        self.set_view_content("(comment (inc 1) (inc 2))")
        self.set_selections((9, 9), (17, 17))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})

        self.eval_context(column=10)
        self.eval_context(column=18)

        self.assertEquals("(inc 1)\n", self.server.recv())
        self.assertEquals("user=> (inc 1)\n", self.get_print())
        self.assertEquals("(inc 2)\n", self.server.recv())
        self.assertEquals("user=> (inc 2)\n", self.get_print())
        self.server.send("2")
        self.assertEquals("2\n", self.get_print())
        self.server.send("3")
        self.assertEquals("3\n", self.get_print())

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
        self.assertEquals("user=> (range 10)\n", self.get_print())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals("(0 1 2 3 4 5 6 7 8 9)\n", self.get_print())

    def test_form(self):
        self.set_view_content("42 84")
        self.set_selections((0, 0), (3, 3))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.eval_context()

        self.assertEquals("user=> 42\n", self.get_print())

        self.eval_context(column=4)

        self.assertEquals("user=> 84\n", self.get_print())

        self.assertEquals("42\n", self.server.recv())
        self.server.send("42")
        self.assertEquals("42\n", self.get_print())
        self.assertEquals("84\n", self.server.recv())
        self.server.send("84")
        self.assertEquals("84\n", self.get_print())

    def test_parameterized(self):
        self.set_view_content("{:a 1} {:b 2}")
        self.set_selections((0, 0), (7, 7))
        self.view.run_command("tutkain_evaluate", {"code": "((requiring-resolve 'clojure.data/diff) $0 $1)"})
        self.eval_context()
        self.assertEquals("((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})\n", self.server.recv())
        self.assertEquals("user=> ((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})\n", self.get_print())
        self.server.send("({:a 1} {:b 2} nil)")
        self.assertEquals("({:a 1} {:b 2} nil)\n", self.get_print())

    def test_eval_in_ns(self):
        self.view.run_command("tutkain_evaluate", {"code": "(reset)", "ns": "user"})
        self.eval_context()

        self.assertEquals("user=> (reset)\n", self.get_print())

        # Clients sends ns first
        ret = self.server.recv()
        self.assertEquals(ret, "(tutkain.repl/switch-ns user)\n")
        self.assertEquals("(reset)\n", self.server.recv())
        self.server.send("nil")
        self.assertEquals("nil\n", self.get_print())

    def test_ns(self):
        self.set_view_content("(ns foo.bar) (ns baz.quux) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "ns"})
        self.eval_context()

        self.assertEquals("user=> (ns foo.bar)\n", self.get_print())

        self.assertEquals("(ns foo.bar)\n", self.server.recv())
        self.eval_context(column=14)

        self.assertEquals("user=> (ns baz.quux)\n", self.get_print())

        self.assertEquals("(ns baz.quux)\n", self.server.recv())

        self.server.send("nil")  # foo.bar
        self.assertEquals("nil\n", self.get_print())
        self.server.send("nil")  # baz.quux
        self.assertEquals("nil\n", self.get_print())

    def test_view(self):
        self.set_view_content("(ns foo.bar) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        message = edn.read(self.backchannel.recv())
        id = message.get(edn.Keyword("id"))

        self.assertEquals({
            edn.Keyword("op"): edn.Keyword("load"),
            edn.Keyword("code"): base64.encode("(ns foo.bar) (defn x [y] y)".encode("utf-8")),
            edn.Keyword("file"): None,
            edn.Keyword("id"): id
        }, message)

        response = edn.kwmap({"id": id, "tag": edn.Keyword("ret"), "val": "nil"})
        self.backchannel.send(response)
        self.assertEquals(response, self.get_print())

    def test_view_syntax_error(self):
        self.set_view_content("(ns foo.bar) (defn x [y] y")  # missing close paren
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        message = edn.read(self.backchannel.recv())

        response = edn.kwmap({
            "id": message.get(edn.Keyword("id")),
            "tag": edn.Keyword("ret"),
            # Can't be bothered to stick a completely realistic exception map
            # here, this'll do
            "val": """{:via [{:type clojure.lang.Compiler$CompilerException, :message "Syntax error reading source at (NO_SOURCE_FILE)"}]}""",
            "exception": True
        })

        self.backchannel.send(response)
        self.assertEquals(response, self.get_print())

    def test_view_common(self):
        self.view.assign_syntax("Packages/Tutkain/Clojure Common (Tutkain).sublime-syntax")
        self.set_view_content("(ns foo.bar) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        response = edn.read(self.backchannel.recv())
        id = response.get(edn.Keyword("id"))

        self.assertEquals({
            edn.Keyword("op"): edn.Keyword("load"),
            edn.Keyword("code"): base64.encode("(ns foo.bar) (defn x [y] y)".encode("utf-8")),
            edn.Keyword("file"): None,
            edn.Keyword("id"): id
        }, response)

        response = edn.kwmap({"id": id, "tag": edn.Keyword("ret"), "val": "#'x"})
        self.backchannel.send(response)
        self.assertEquals(response, self.get_print())

    def test_discard(self):
        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=3)

        self.assertEquals("user=> (inc 1)\n", self.get_print())
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals("2\n", self.get_print())

        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.eval_context(column=3)

        self.assertEquals("user=> (inc 1)\n", self.get_print())
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals("2\n", self.get_print())

        self.set_view_content("(inc #_(dec 2) 4)")
        self.set_selections((14, 14))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=8)

        self.assertEquals("user=> (dec 2)\n", self.get_print())
        self.assertEquals("(dec 2)\n", self.server.recv())
        self.server.send("1")
        self.assertEquals("1\n", self.get_print())

        self.set_view_content("#_:a")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.eval_context(column=3)

        self.assertEquals("user=> :a\n", self.get_print())
        self.assertEquals(":a\n", self.server.recv())
        self.server.send(":a")
        self.assertEquals(":a\n", self.get_print())

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
                edn.Keyword("ident"): "rand",
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
            edn.Keyword("ident"): "map",
            edn.Keyword("ns"): None,
            edn.Keyword("dialect"): edn.Keyword("clj"),
            edn.Keyword("id"): response.get(edn.Keyword("id"))
        }, response)

    # def test_issue_46(self):
    #     n = io.DEFAULT_BUFFER_SIZE + 1024
    #     code = """(apply str (repeat {n} "x"))"""
    #     self.set_view_content(code)
    #     self.set_selections((0, 0))
    #     self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
    #     self.eval_context()

    #     self.assertEquals(f"user=> {code}\n", self.get_print())

    #     self.assertEquals(code + "\n", self.server.recv())
    #     response = "x" * n
    #     self.server.send(response)

    #     chunks = [
    #         response[i:i + io.DEFAULT_BUFFER_SIZE] for i in range(0, len(response), io.DEFAULT_BUFFER_SIZE)
    #     ]

    #     for chunk in chunks[:-1]:
    #         self.assertEquals(chunk, self.get_print())

    #     self.assertEquals(chunks[-1] + "\n", self.get_print())

    def test_evaluate_dialect(self):
        self.view.run_command("tutkain_evaluate", {"code": "(random-uuid)", "dialect": "cljs"})
        # The server and the client receive no messages because the evaluation
        # uses a different dialect than the server.
        self.assertRaises(queue.Empty, lambda: self.client.printq.get_nowait())
        self.assertRaises(queue.Empty, lambda: self.server.recvq.get_nowait())
        self.view.run_command("tutkain_evaluate", {"code": """(Integer/parseInt "42")""", "dialect": "clj"})
        self.eval_context()
        self.assertEquals("""(Integer/parseInt "42")\n""", self.server.recv())
        self.assertEquals("""user=> (Integer/parseInt "42")\n""", self.get_print())

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

        response = edn.kwmap({
            "id": id,
            "tag": edn.Keyword("ret"),
            "val": "{:test 1, :pass 1, :fail 0, :error 0, :assert 1, :type :summary}",
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
        })

        self.backchannel.send(response)

        self.assertEquals(response, self.get_print())

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

        response = edn.kwmap({
            "id": id,
            "tag": edn.Keyword("ret"),
            "val": "{:test 1, :pass 0, :fail 1, :error 0, :assert 1, :type :summary}",
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
        })

        self.backchannel.send(response)

        self.assertEquals(response, self.get_print())
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

    def test_apropos(self):
        self.view.window().run_command("tutkain_apropos", {"pattern": "cat"})

        op = edn.read(self.backchannel.recv())
        id = op.get(edn.Keyword("id"))

        self.assertEquals(edn.kwmap({
            "op": edn.Keyword("apropos"),
            "id": id,
            "pattern": "cat"
        }), op)

        # TODO: This is not useful at the moment. How do we test things like
        # this that go into a quick panel and not in the REPL view? Should
        # they also go through printq (or equivalent)?
        self.backchannel.send(edn.kwmap({
            "vars": [edn.kwmap({
                "name": edn.Symbol("cat"),
                "file": "jar:file:/home/.m2/repository/org/clojure/clojure/1.11.0-alpha1/clojure-1.11.0-alpha1.jar!/clojure/core.clj",
                "column": 1,
                "line": 7644,
                "arglists": ["[rf]"],
                "doc": ["A transducer which concatenates the contents of each input, which must be a\\n  collection, into the reduction."],
                "type": "function",
                "ns": "clojure.core"
            })]
        }))

        print(self.get_print())


class TestJSClient(PackageTestCase):
    def get_print(self):
        return self.client.printq.get(timeout=5)

    @classmethod
    def conduct_handshake(self):
        server = self.server

        # Client starts clojure.main/repl
        server.recv()

        # Client requests build IDs
        server.recv()

        # Server sends build ID list
        server.send("[:browser, :node-script, :npm]")

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

        # Client starts REPL
        server.recv()

        with Server(send_edn) as backchannel:
            server.send(f"""{{:greeting "ClojureScript 1.10.844" :host "localhost", :port {backchannel.port}}}""")

            for _ in range(4):
                backchannel.recv()

            # TODO: Add test for no runtime

            # ClojureScript version info is printed on the client
            self.client.printq.get(timeout=5)

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

        self.server = Server(send_text, greeting=write_greeting)

        self.server.start()

        self.client = repl.JSClient(
            source_root(),
            self.server.host,
            self.server.port,
            lambda _, on_done: on_done(1)
        )

        self.server.executor.submit(self.client.connect)

        dialect = edn.Keyword("cljs")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, self.client.host, self.client.port)
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
        self.assertEquals("user=> (range 10)\n", self.get_print())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals("(0 1 2 3 4 5 6 7 8 9)\n", self.get_print())


class TestBabashkaClient(PackageTestCase):
    def get_print(self):
        return self.client.printq.get(timeout=5)

    @classmethod
    def conduct_handshake(self):
        server = self.server

        # Client starts io-prepl
        server.recv()

        # Client sends version print
        server.recv()

        # Server responds
        server.send("""Babashka 0.3.6""")
        server.send("nil")

        # Babashka version info is printed on the client
        self.client.printq.get(timeout=5)

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

        self.server = Server(send_text, greeting=write_greeting)

        self.server.start()

        self.client = repl.BabashkaClient(
            source_root(),
            self.server.host,
            self.server.port
        )

        self.server.executor.submit(self.client.connect)
        dialect = edn.Keyword("bb")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, self.client.host, self.client.port)
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

        self.assertEquals(
            edn.kwmap({"tag": edn.Keyword("out"), "val": "user=> (range 10)\n"}),
            self.get_print()
        )

        self.server.send("(0 1 2 3 4 5 6 7 8 9)")

        self.assertEquals(
            edn.kwmap({
                "tag": edn.Keyword("out"),
                "val": "(0 1 2 3 4 5 6 7 8 9)\n"
            }),
            self.get_print()
        )
