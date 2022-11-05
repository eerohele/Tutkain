import sublime
import os
import queue
import unittest
import unittesting
import tempfile
import time

from Tutkain.api import edn
from Tutkain.src import repl
from Tutkain.src.repl import formatter
from Tutkain.src import base64
from Tutkain.src import test

from .mock import JvmBackchannelServer, JvmServer
from .util import PackageTestCase


def select_keys(d, ks):
    return {k: d[k] for k in ks}


def input(val):
    return edn.kwmap({"tag": edn.Keyword("in"), "val": val})


def ret(val):
    return edn.kwmap({"tag": edn.Keyword("ret"), "val": val})


class TestJVMClient(PackageTestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.window = sublime.active_window()
        server = JvmBackchannelServer().start()
        self.client = repl.JVMClient(server.host, server.port)
        self.output_view = repl.views.get_or_create_view(self.window, "view")
        repl.start(self.output_view, self.client)
        self.server = server.connection.result(timeout=5)
        self.client.printq.get(timeout=5)

        self.addClassCleanup(repl.stop, self.window)
        self.addClassCleanup(self.server.backchannel.stop)
        self.addClassCleanup(self.server.stop)

    def get_print(self):
        return self.client.printq.get(timeout=5)

    # @unittest.SkipTest
    def test_eval_context_file(self):
        file = os.path.join(tempfile.gettempdir(), "my.clj")
        self.view.retarget(file)
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.assertEquals(input("(inc 1)\n"), self.get_print())
        self.eval_context(file=file)
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

    # @unittest.SkipTest
    def test_outermost(self):
        self.set_view_content("(comment (inc 1) (inc 2))")
        self.set_selections((9, 9), (17, 17))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.assertEquals(input("(inc 1)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals(input("(inc 2)\n"), self.get_print())
        self.eval_context(column=18)
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals("(inc 2)\n", self.server.recv())
        self.server.send("3")
        self.assertEquals(ret("2\n"), self.get_print())
        self.assertEquals(ret("3\n"), self.get_print())

    # @unittest.SkipTest
    def test_outermost_empty(self):
        self.set_view_content("")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.assertRaises(queue.Empty, lambda: self.server.recvq.get_nowait())

    # @unittest.SkipTest
    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals(input("(range 10)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals("(range 10)\n", self.server.recv())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals(ret("(0 1 2 3 4 5 6 7 8 9)\n"), self.get_print())

    # @unittest.SkipTest
    def test_up_to_point(self):
        self.set_view_content("()")
        self.set_selections((1, 1))
        self.view.run_command("tutkain_evaluate", {"scope": "up_to_point"})
        self.assertEquals(input("()\n"), self.get_print())
        self.eval_context(column=2)
        self.assertEquals("()\n", self.server.recv())
        self.server.send("()")
        self.assertEquals(ret("()\n"), self.get_print())

        self.set_view_content("(-> 1 inc dec)")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "up_to_point"})
        self.assertEquals(input("(-> 1 inc)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals("(-> 1 inc)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

        self.set_view_content("(-> 1 inc dec) (-> 2 dec inc)")
        self.set_selections((9, 9), (24, 24))
        self.view.run_command("tutkain_evaluate", {"scope": "up_to_point"})
        self.assertEquals(input("(-> 1 inc)\n"), self.get_print())
        self.assertEquals(input("(-> 2 dec)\n"), self.get_print())
        self.eval_context(column=10)
        self.eval_context(column=25)
        self.assertEquals("(-> 1 inc)\n", self.server.recv())
        self.assertEquals("(-> 2 dec)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())
        self.server.send("1")
        self.assertEquals(ret("1\n"), self.get_print())

        self.set_selections((0, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "up_to_point"})
        self.assertEquals(input("(-> 1 inc)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals("(-> 1 inc)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

        self.set_selections((1, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "up_to_point"})
        self.assertEquals(input("(-> 1 inc)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals("(-> 1 inc)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

        self.set_view_content("(a) (b) (c)")
        self.set_selections((7, 7))
        self.view.run_command("tutkain_evaluate", {"scope": "up_to_point"})
        self.assertEquals(input("(a) (b)\n"), self.get_print())
        self.eval_context(column=8)
        self.assertEquals("(a) (b)\n", self.server.recv())
        self.server.send("1")
        self.assertEquals(ret("1\n"), self.get_print())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

        self.view.assign_syntax("Markdown.sublime-syntax")
        self.set_view_content(
            """```clojure
1
2
```"""
        )
        self.set_selections((12, 12))
        self.view.run_command("tutkain_evaluate", {"scope": "up_to_point"})
        self.assertEquals(input("1\n"), self.get_print())
        self.eval_context(line=2, column=2)
        self.assertEquals("1\n", self.server.recv())
        self.server.send("1")
        self.assertEquals(ret("1\n"), self.get_print())

    # @unittest.SkipTest
    def test_empty_string(self):
        self.set_view_content(" ")
        self.set_selections((0, 1))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertRaises(queue.Empty, lambda: self.client.printq.get_nowait())
        self.assertRaises(queue.Empty, lambda: self.server.recvq.get_nowait())
        self.assertRaises(
            queue.Empty, lambda: self.server.backchannel.recvq.get_nowait()
        )

    # @unittest.SkipTest
    def test_form(self):
        self.set_view_content("42 84")
        self.set_selections((0, 0), (3, 3))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.assertEquals(input("42\n"), self.get_print())
        self.eval_context()
        self.assertEquals(input("84\n"), self.get_print())
        self.eval_context(column=4)
        self.assertEquals("42\n", self.server.recv())
        self.server.send("42")
        self.assertEquals(ret("42\n"), self.get_print())
        self.assertEquals("84\n", self.server.recv())
        self.server.send("84")
        self.assertEquals(ret("84\n"), self.get_print())

    # @unittest.SkipTest
    def test_ns_variable(self):
        self.set_view_content("(ns foo.bar)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"code": "(in-ns '${ns})"})
        self.assertEquals(input("(in-ns 'foo.bar)\n"), self.get_print())
        self.eval_context(ns=edn.Symbol("foo.bar"))
        self.assertEquals("(in-ns 'foo.bar)\n", self.server.recv())
        self.server.send("""#object[clojure.lang.Namespace 0x4a1c0752 "foo.bar"]""")
        self.assertEquals(
            ret("""#object[clojure.lang.Namespace 0x4a1c0752 "foo.bar"]\n"""),
            self.get_print(),
        )

    # @unittest.SkipTest
    def test_file_variable(self):
        file = os.path.join(tempfile.gettempdir(), "my.clj")
        self.view.retarget(file)
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command(
            "tutkain_evaluate",
            {"code": """((requiring-resolve 'cognitect.transcriptor/run) "${file}")"""},
        )
        self.assertEquals(
            input(f"""((requiring-resolve 'cognitect.transcriptor/run) "{file}")\n"""),
            self.get_print(),
        )
        self.eval_context(file=file)
        self.assertEquals(
            f"""((requiring-resolve 'cognitect.transcriptor/run) "{file}")\n""",
            self.server.recv(),
        )
        self.server.send("nil")
        self.assertEquals(ret("nil\n"), self.get_print())

    # @unittest.SkipTest
    def test_parameterized(self):
        self.set_view_content("{:a 1} {:b 2}")
        self.set_selections((0, 0), (7, 7))
        self.view.run_command(
            "tutkain_evaluate",
            {"code": "((requiring-resolve 'clojure.data/diff) $0 $1)"},
        )
        self.assertEquals(
            input("((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})\n"),
            self.get_print(),
        )
        self.eval_context()
        self.assertEquals(
            "((requiring-resolve 'clojure.data/diff) {:a 1} {:b 2})\n",
            self.server.recv(),
        )
        self.server.send("({:a 1} {:b 2} nil)")
        self.assertEquals(ret("({:a 1} {:b 2} nil)\n"), self.get_print())

    # @unittest.SkipTest
    def test_eval_in_ns(self):
        self.view.run_command("tutkain_evaluate", {"code": "(reset)", "ns": "foo.bar"})
        self.assertEquals(input("(reset)\n"), self.get_print())
        self.eval_context(ns=edn.Symbol("foo.bar"))
        self.assertEquals("(reset)\n", self.server.recv())
        self.server.send("nil")
        self.assertEquals(ret("nil\n"), self.get_print())

    # @unittest.SkipTest
    def test_ns(self):
        self.set_view_content("(ns foo.bar) (ns baz.quux) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "ns"})
        self.assertEquals(input("(ns foo.bar)\n"), self.get_print())
        self.eval_context(ns=edn.Symbol("foo.bar"))
        self.assertEquals(input("(ns baz.quux)\n"), self.get_print())
        # TODO: ns here is unintuitive, should be baz.quux maybe?
        self.eval_context(column=14, ns=edn.Symbol("foo.bar"))
        self.assertEquals("(ns foo.bar)\n", self.server.recv())
        self.assertEquals("(ns baz.quux)\n", self.server.recv())
        self.server.send("nil")  # foo.bar
        self.assertEquals(ret("nil\n"), self.get_print())
        self.server.send("nil")  # baz.quux
        self.assertEquals(ret("nil\n"), self.get_print())

    # @unittest.SkipTest
    def test_view(self):
        self.set_view_content("(ns foo.bar) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        message = edn.read(self.server.backchannel.recv())
        id = message.get(edn.Keyword("id"))

        self.assertEquals(
            {
                edn.Keyword("op"): edn.Keyword("load"),
                edn.Keyword("code"): base64.encode(
                    "(ns foo.bar) (defn x [y] y)".encode("utf-8")
                ),
                edn.Keyword("file"): None,
                edn.Keyword("id"): id,
            },
            message,
        )

        response = edn.kwmap({"id": id, "tag": edn.Keyword("ret"), "val": "nil"})
        self.server.backchannel.send(response)

    # @unittest.SkipTest
    def test_view_syntax_error(self):
        self.set_view_content("(ns foo.bar) (defn x [y] y")  # missing close paren
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        message = edn.read(self.server.backchannel.recv())
        id = message.get(edn.Keyword("id"))

        self.assertEquals(
            {
                edn.Keyword("op"): edn.Keyword("load"),
                edn.Keyword("code"): base64.encode(
                    "(ns foo.bar) (defn x [y] y".encode("utf-8")
                ),
                edn.Keyword("file"): None,
                edn.Keyword("id"): id,
            },
            message,
        )

        # Can't be bothered to stick a completely realistic exception map
        # here, this'll do
        ex_message = """{:via [{:type clojure.lang.Compiler$CompilerException, :message "Syntax error reading source at (NO_SOURCE_FILE)"}]}"""

        response = edn.kwmap(
            {"id": id, "tag": edn.Keyword("ret"), "val": ex_message, "exception": True}
        )

        self.server.backchannel.send(response)
        self.assertEquals(response, self.get_print())

    # @unittest.SkipTest
    def test_view_common(self):
        self.view.assign_syntax(
            "Packages/Tutkain/Clojure Common (Tutkain).sublime-syntax"
        )
        self.set_view_content("(ns baz.quux) (defn x [y] y)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "view"})

        message = edn.read(self.server.backchannel.recv())
        id = message.get(edn.Keyword("id"))

        self.assertEquals(
            {
                edn.Keyword("op"): edn.Keyword("load"),
                edn.Keyword("code"): base64.encode(
                    "(ns baz.quux) (defn x [y] y)".encode("utf-8")
                ),
                edn.Keyword("file"): None,
                edn.Keyword("id"): id,
            },
            message,
        )

        response = edn.kwmap(
            {"id": id, "tag": edn.Keyword("ret"), "val": "#'baz.quux/x"}
        )
        self.server.backchannel.send(response)

    # @unittest.SkipTest
    def test_discard(self):
        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals(input("(inc 1)\n"), self.get_print())
        self.eval_context(column=3)

        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

        self.set_view_content("#_(inc 1)")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.assertEquals(input("(inc 1)\n"), self.get_print())
        self.eval_context(column=3)

        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

        self.set_view_content("(inc #_(dec 2) 4)")
        self.set_selections((14, 14))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals(input("(dec 2)\n"), self.get_print())
        self.eval_context(column=8)

        self.assertEquals("(dec 2)\n", self.server.recv())
        self.server.send("1")
        self.assertEquals(ret("1\n"), self.get_print())

        self.set_view_content("#_:a")
        self.set_selections((2, 2))
        self.view.run_command("tutkain_evaluate", {"scope": "form"})
        self.assertEquals(input(":a\n"), self.get_print())
        self.eval_context(column=3)

        self.assertEquals(":a\n", self.server.recv())
        self.server.send(":a")
        self.assertEquals(ret(":a\n"), self.get_print())

    # @unittest.SkipTest
    def test_lookup(self):
        self.set_view_content("(rand)")

        for n in range(1, 5):
            self.set_selections((n, n))

            self.view.run_command(
                "tutkain_show_information", {"selector": "variable.function"}
            )

            response = edn.read(self.server.backchannel.recv())

            self.assertEquals(
                {
                    edn.Keyword("op"): edn.Keyword("lookup"),
                    edn.Keyword("ident"): "rand",
                    edn.Keyword("ns"): None,
                    edn.Keyword("dialect"): edn.Keyword("clj"),
                    edn.Keyword("id"): response.get(edn.Keyword("id")),
                },
                response,
            )

    # @unittest.SkipTest
    def test_lookup_var(self):
        self.set_view_content("#'foo/bar")

        for n in range(0, 9):
            self.set_selections((n, n))

            self.view.run_command("tutkain_show_information")

            response = edn.read(self.server.backchannel.recv())

            self.assertEquals(
                {
                    edn.Keyword("op"): edn.Keyword("lookup"),
                    edn.Keyword("ident"): "foo/bar",
                    edn.Keyword("ns"): None,
                    edn.Keyword("dialect"): edn.Keyword("clj"),
                    edn.Keyword("id"): response.get(edn.Keyword("id")),
                },
                response,
            )

    # @unittest.SkipTest
    def test_lookup_head(self):
        self.set_view_content("(map inc )")
        self.set_selections((9, 9))

        self.view.run_command(
            "tutkain_show_information",
            {"selector": "variable.function", "seek_backward": True},
        )

        response = edn.read(self.server.backchannel.recv())

        self.assertEquals(
            {
                edn.Keyword("op"): edn.Keyword("lookup"),
                edn.Keyword("ident"): "map",
                edn.Keyword("ns"): None,
                edn.Keyword("dialect"): edn.Keyword("clj"),
                edn.Keyword("id"): response.get(edn.Keyword("id")),
            },
            response,
        )

    # @unittest.SkipTest
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

    # @unittest.SkipTest
    def test_evaluate_dialect(self):
        self.view.run_command(
            "tutkain_evaluate", {"code": "(random-uuid)", "dialect": "cljs"}
        )
        # The server and the client receive no messages because the evaluation
        # uses a different dialect than the server.
        self.assertRaises(queue.Empty, lambda: self.client.printq.get_nowait())
        self.assertRaises(queue.Empty, lambda: self.server.recvq.get_nowait())
        self.view.run_command(
            "tutkain_evaluate",
            {"code": """(Integer/parseInt "42")""", "dialect": "clj"},
        )
        self.assertEquals(input("""(Integer/parseInt "42")\n"""), self.get_print())
        self.eval_context()
        self.assertEquals("""(Integer/parseInt "42")\n""", self.server.recv())
        self.server.send("""42""")
        self.assertEquals(ret("""42\n"""), self.get_print())

    # @unittest.SkipTest
    def test_async_run_tests_ns(self):
        code = """
        (ns my.app
          (:require [clojure.test :refer [deftest is]]))

        (deftest my-test
          (is (= 2 (+ 1 1))))
        """

        self.set_view_content(code)
        self.view.run_command("tutkain_run_tests", {"scope": "ns"})
        message = edn.read(self.server.backchannel.recv())
        id = message.get(edn.Keyword("id"))

        self.assertEquals(
            edn.kwmap(
                {
                    "op": edn.Keyword("test"),
                    "file": None,
                    "ns": "my.app",
                    "vars": [],
                    "code": base64.encode(code.encode("utf-8")),
                    "id": id,
                }
            ),
            message,
        )

        response = edn.kwmap(
            {
                "id": id,
                "tag": edn.Keyword("ret"),
                "val": "{:test 1, :pass 1, :fail 0, :error 0, :assert 1, :type :summary}",
                "pass": [
                    edn.kwmap(
                        {
                            "type": edn.Keyword("pass"),
                            "line": 5,
                            "var-meta": edn.kwmap(
                                {
                                    "line": 4,
                                    "column": 1,
                                    "file": "NO_SOURCE_FILE",
                                    "name": edn.Symbol("my-test"),
                                    "ns": "my.app",
                                }
                            ),
                        }
                    )
                ],
                "fail": [],
                "error": [],
            }
        )

        self.server.backchannel.send(response)
        yield unittesting.AWAIT_WORKER  # Why?

        self.assertEquals([sublime.Region(78, 78)], test.regions(self.view, "passes"))

        self.assertFalse(test.regions(self.view, "fail"))
        self.assertFalse(test.regions(self.view, "error"))

    # @unittest.SkipTest
    def test_run_tests_view_error(self):
        code = """
        (ns my.app
          (:require [clojure.test :refer [deftest is]]))

        (deftest my-test
          (is (= foo (+ 1 1))))
        """

        self.set_view_content(code)
        self.view.run_command("tutkain_run_tests", {"scope": "ns"})
        message = edn.read(self.server.backchannel.recv())
        id = message.get(edn.Keyword("id"))

        self.assertEquals(
            edn.kwmap(
                {
                    "op": edn.Keyword("test"),
                    "file": None,
                    "ns": "my.app",
                    "vars": [],
                    "code": base64.encode(code.encode("utf-8")),
                    "id": id,
                }
            ),
            message,
        )

        response = edn.kwmap(
            {
                "id": id,
                "tag": edn.Keyword("ret"),
                "val": """{:via [{:type clojure.lang.Compiler$CompilerException, :message "Syntax error compiling at (NO_SOURCE_FILE:5:3).", :data #:clojure.error{:phase :compile-syntax-check, :line 5, :column 3, :source "NO_SOURCE_FILE"}, :at [clojure.lang.Compiler analyze "Compiler.java" 6812]} {:type java.lang.RuntimeException, :message "Unable to resolve symbol: foo in this context", :at [clojure.lang.Util runtimeException "Util.java" 221]}], :trace [[clojure.lang.Util runtimeException "Util.java" 221] [clojure.lang.Compiler resolveIn "Compiler.java" 7418] [clojure.lang.Compiler resolve "Compiler.java" 7362]], :cause "Unable to resolve symbol: foo in this context", :phase :execution}""",
                "exception": True,
            }
        )

        self.server.backchannel.send(response)
        yield unittesting.AWAIT_WORKER  # Why?

        self.assertFalse(test.regions(self.view, "passes"))
        self.assertFalse(test.regions(self.view, "fail"))
        self.assertFalse(test.regions(self.view, "error"))
        self.assertEquals(response, self.get_print())

    # @unittest.SkipTest
    def test_async_unsuccessful_tests(self):
        code = """
        (ns my.app
          (:require [clojure.test :refer [deftest is]]))

        (deftest my-test
          (is (= 3 (+ 1 1))))
        """

        self.set_view_content(code)
        self.view.run_command("tutkain_run_tests", {"scope": "ns"})
        response = edn.read(self.server.backchannel.recv())
        id = response.get(edn.Keyword("id"))

        self.assertEquals(
            edn.kwmap(
                {
                    "op": edn.Keyword("test"),
                    "file": None,
                    "ns": "my.app",
                    "vars": [],
                    "code": base64.encode(code.encode("utf-8")),
                    "id": id,
                }
            ),
            response,
        )

        response = edn.kwmap(
            {
                "id": id,
                "tag": edn.Keyword("ret"),
                "val": "{:test 1, :pass 0, :fail 1, :error 0, :assert 1, :type :summary}",
                "pass": [],
                "fail": [
                    edn.kwmap(
                        {
                            "file": None,
                            "type": edn.Keyword("fail"),
                            "line": 5,
                            "expected": "3\\n",
                            "actual": "2\\n",
                            "message": None,
                            "var-meta": edn.kwmap(
                                {
                                    "line": 4,
                                    "column": 1,
                                    "file": "NO_SOURCE_FILE",
                                    "name": edn.Symbol("my-test"),
                                    "ns": "my.app",
                                }
                            ),
                        }
                    )
                ],
                "error": [],
            }
        )

        self.server.backchannel.send(response)
        yield unittesting.AWAIT_WORKER  # Why?

        self.assertEquals([sublime.Region(78, 78)], test.regions(self.view, "failures"))

        self.assertEquals(
            [{"name": "my-test", "region": [78, 78], "type": "fail"}],
            test.unsuccessful(self.view),
        )

        self.assertFalse(test.regions(self.view, "passes"))
        self.assertFalse(test.regions(self.view, "error"))

    # @unittest.SkipTest
    def test_apropos(self):
        self.view.window().run_command("tutkain_apropos", {"pattern": "cat"})

        op = edn.read(self.server.backchannel.recv())
        id = op.get(edn.Keyword("id"))

        self.assertEquals(
            edn.kwmap({"op": edn.Keyword("apropos"), "id": id, "pattern": "cat"}), op
        )

        # TODO: This is not useful at the moment. How do we test things like
        # this that go into a quick panel and not in the REPL view? Should
        # they also go through printq (or equivalent)?
        self.server.backchannel.send(
            edn.kwmap(
                {
                    "vars": [
                        edn.kwmap(
                            {
                                "name": edn.Symbol("cat"),
                                "file": "jar:file:/home/.m2/repository/org/clojure/clojure/1.11.0-alpha1/clojure-1.11.0-alpha1.jar!/clojure/core.clj",
                                "column": 1,
                                "line": 7644,
                                "arglists": ["[rf]"],
                                "doc": [
                                    "A transducer which concatenates the contents of each input, which must be a\\n  collection, into the reduction."
                                ],
                                "type": "function",
                                "ns": "clojure.core",
                            }
                        )
                    ]
                }
            )
        )

        print(self.get_print())

    # @unittest.SkipTest
    def test_evaluate_to_clipboard(self):
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command(
            "tutkain_evaluate", {"scope": "outermost", "output": "clipboard"}
        )
        self.assertEquals(input("(inc 1)\n"), self.get_print())
        # Client sends eval context over backchannel
        eval_context = edn.read(self.server.backchannel.recv())

        self.assertEquals(
            edn.kwmap(
                {
                    "op": edn.Keyword("set-eval-context"),
                    "file": "NO_SOURCE_FILE",
                    "line": 1,
                    "column": 1,
                    "response": edn.kwmap({"output": edn.Keyword("clipboard")}),
                }
            ),
            select_keys(
                eval_context,
                [
                    edn.Keyword("op"),
                    edn.Keyword("file"),
                    edn.Keyword("line"),
                    edn.Keyword("column"),
                    edn.Keyword("response"),
                ],
            ),
        )

        # Backchannel sends eval context response
        self.server.backchannel.send(
            edn.kwmap(
                {"id": eval_context.get(edn.Keyword("id")), "result": edn.Keyword("ok")}
            )
        )

        # Client sends code string over eval channel
        self.assertEquals("(inc 1)\n", self.server.recv())

        # Server sends response over backchannel
        response = edn.kwmap(
            {
                "output": edn.Keyword("clipboard"),
                "tag": edn.Keyword("ret"),
                "string": "2",
                "val": "2\n",
            }
        )

        self.server.backchannel.send(response)

        self.assertEquals(response, self.get_print())

    # @unittest.SkipTest
    def test_evaluate_to_inline(self):
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command(
            "tutkain_evaluate", {"scope": "outermost", "inline_result": True}
        )
        self.assertEquals(input("(inc 1)\n"), self.get_print())

        # Client sends eval context over backchannel
        eval_context = edn.read(self.server.backchannel.recv())

        self.assertEquals(
            edn.kwmap(
                {
                    "op": edn.Keyword("set-eval-context"),
                    "file": "NO_SOURCE_FILE",
                    "line": 1,
                    "column": 1,
                    "response": edn.kwmap(
                        {
                            "point": 7,
                            "output": edn.Keyword("inline"),
                            "view-id": self.view.id(),
                        }
                    ),
                }
            ),
            select_keys(
                eval_context,
                [
                    edn.Keyword("op"),
                    edn.Keyword("file"),
                    edn.Keyword("line"),
                    edn.Keyword("column"),
                    edn.Keyword("response"),
                ],
            ),
        )

        # Backchannel sends eval context response
        self.server.backchannel.send(
            edn.kwmap(
                {"id": eval_context.get(edn.Keyword("id")), "result": edn.Keyword("ok")}
            )
        )

        # Client sends code string over eval channel
        self.assertEquals("(inc 1)\n", self.server.recv())

        view_id = eval_context.get(edn.Keyword("response")).get(edn.Keyword("view-id"))

        # Server sends response over backchannel
        response = edn.kwmap(
            {
                "tag": edn.Keyword("ret"),
                "val": "2",
                "output": eval_context.get(edn.Keyword("response")).get(
                    edn.Keyword("output")
                ),
                "view-id": view_id,
                "point": 7,
            }
        )

        self.server.backchannel.send(response)

        self.assertEquals(response, self.get_print())

    # @unittest.SkipTest
    def test_evaluate_code_to_inline(self):
        self.set_view_content("(inc 1)")
        self.set_selections((7, 7))
        self.view.run_command(
            "tutkain_evaluate", {"code": "(inc 1)", "inline_result": True}
        )
        self.assertEquals(input("(inc 1)\n"), self.get_print())

        # Client sends eval context over backchannel
        eval_context = edn.read(self.server.backchannel.recv())

        self.assertEquals(
            edn.kwmap(
                {
                    "op": edn.Keyword("set-eval-context"),
                    "file": "NO_SOURCE_FILE",
                    "line": 1,
                    "column": 1,
                    "response": edn.kwmap(
                        {
                            "point": 7,
                            "output": edn.Keyword("inline"),
                            "view-id": self.view.id(),
                        }
                    ),
                }
            ),
            select_keys(
                eval_context,
                [
                    edn.Keyword("op"),
                    edn.Keyword("file"),
                    edn.Keyword("line"),
                    edn.Keyword("column"),
                    edn.Keyword("response"),
                ],
            ),
        )

        # Backchannel sends eval context response
        self.server.backchannel.send(
            edn.kwmap(
                {"id": eval_context.get(edn.Keyword("id")), "result": edn.Keyword("ok")}
            )
        )

        # Client sends code string over eval channel
        self.assertEquals("(inc 1)\n", self.server.recv())

        view_id = eval_context.get(edn.Keyword("response")).get(edn.Keyword("view-id"))

        # Server sends response over backchannel
        response = edn.kwmap(
            {
                "tag": edn.Keyword("ret"),
                "val": "2",
                "output": eval_context.get(edn.Keyword("response")).get(
                    edn.Keyword("output")
                ),
                "view-id": view_id,
                "point": 7,
            }
        )

        self.server.backchannel.send(response)

        self.assertEquals(response, self.get_print())

    # @unittest.SkipTest
    def test_mark_outermost(self):
        self.set_view_content("(comment (inc 1))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_mark_form")
        self.view.run_command("tutkain_evaluate", {"scope": "mark"})
        self.assertEquals(input("(inc 1)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())

    # @unittest.SkipTest
    def test_mark_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_mark_form", {"scope": "innermost"})
        self.view.run_command("tutkain_evaluate", {"scope": "mark"})
        self.assertEquals(input("(range 10)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals("(range 10)\n", self.server.recv())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals(ret("(0 1 2 3 4 5 6 7 8 9)\n"), self.get_print())

    # @unittest.SkipTest
    def test_mark_ns_file(self):
        file = os.path.join(tempfile.gettempdir(), "my.clj")
        self.view.retarget(file)
        self.set_view_content("(ns foo.bar) (inc 1)")
        self.set_selections((13, 13))
        self.view.run_command("tutkain_mark_form")
        self.view.run_command("tutkain_evaluate", {"scope": "mark"})
        self.assertEquals(input("(inc 1)\n"), self.get_print())
        self.eval_context(ns=edn.Symbol("foo.bar"), column=14, file=file)
        self.assertEquals("(inc 1)\n", self.server.recv())
        self.server.send("2")
        self.assertEquals(ret("2\n"), self.get_print())


class TestNoBackchannelJVMClient(PackageTestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.window = sublime.active_window()
        server = JvmServer().start()
        self.client = repl.JVMClient(
            server.host, server.port, options={"backchannel": {"enabled": False}}
        )
        self.output_view = repl.views.get_or_create_view(self.window, "view")
        repl.start(self.output_view, self.client)
        self.server = server.connection.result(timeout=5)
        self.client.printq.get(timeout=5)  # Swallow the initial prompt

        self.addClassCleanup(repl.stop, self.window)
        self.addClassCleanup(self.server.stop)

    def get_print(self):
        return self.client.printq.get(timeout=5)

    # @unittest.SkipTest
    def test_outermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate", {"scope": "outermost"})
        self.assertEquals(input("(map inc (range 10))\n"), self.get_print())
        self.assertEquals("(map inc (range 10))\n", self.server.recv())
        self.server.send("(1 2 3 4 5 6 7 8 9 10)")
        self.assertEquals(ret("(1 2 3 4 5 6 7 8 9 10)\n"), self.get_print())
