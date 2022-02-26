from .mock import JsBackchannelServer, JvmBackchannelServer, JvmServer
from Tutkain.api import edn
from Tutkain.src import repl
from Tutkain.src import settings
from Tutkain.src import state

from concurrent import futures

import sublime
import sys
import textwrap
import types
import unittesting
import unittest


class TestCase(unittesting.DeferrableTestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.executor = futures.ThreadPoolExecutor()
        self.original_settings = settings.load().to_dict()

    @classmethod
    def tearDownClass(self):
        self.executor.shutdown(wait=False)

    def tearDown(self):
        super().tearDown()
        settings.load().update(self.original_settings)

    def close_window(self, window):
        window.destroy_output_panel("tutkain.tap_panel")
        window.destroy_output_panel(repl.views.output_panel_name())
        window.run_command("close_window")

    def make_window(self):
        sublime.run_command("new_window")
        window = sublime.active_window()
        window.run_command("show_panel", {"panel": "console"})
        return window

    def make_scratch_view(self, window, syntax="Clojure (Tutkain).sublime-syntax"):
        view = window.new_file()
        view.set_name("*scratch*")
        view.set_scratch(True)
        view.sel().clear()
        view.window().focus_view(view)
        view.assign_syntax(syntax)
        return view

    def content(self, view):
        return view and view.substr(sublime.Region(0, view.size()))

    def clear_view(self, view):
        view.run_command("select_all")
        view.run_command("right_delete")

    def set_view_content(self, view, characters):
        self.clear_view(view)
        view.run_command("append", {"characters": characters})

    def set_selections(self, view, *pairs):
        view.sel().clear()

        for begin, end in pairs:
            view.sel().add(sublime.Region(begin, end))


class TestConnectDisconnect(TestCase):
    def connect(self, window, args):
        dialect = args.get("dialect", "clj")

        if not args.get("backchannel", True):
            server = JvmServer().start()
        elif dialect == "cljs":
            server = JsBackchannelServer().start()
        else:
            server = JvmBackchannelServer().start()

        default_args = {"host": server.host, "port": server.port}
        window.run_command("tutkain_connect", {**default_args, **args})
        return server.connection.result(timeout=3)

    def disconnect(self, window):
        window.run_command("tutkain_disconnect")

    def eval_context(self, backchannel, ns=edn.Symbol("user"), file="NO_SOURCE_FILE", line=1, column=1):
        actual = edn.read(backchannel.recv())
        id = actual.get(edn.Keyword("id"))

        response = edn.kwmap({
             "id": id,
             "op": edn.Keyword("set-eval-context"),
             "file": file,
             "ns": ns,
             "line": line,
             "column": column,
        })

        self.assertEquals(response, actual)

        response = edn.kwmap({
            "id": id,
            "file": file,
            "thread-bindings": edn.kwmap({
                "ns": ns,
                "file": file
            })
        })

        backchannel.send(response)

    def output_panel(self, window):
        return window.find_output_panel(repl.views.output_panel_name())

    # FIXME: Remove, quite unnecessary
    def equals(self, expected, actual):
        return expected == actual

    def gutter_marks(self, view, tag):
        if view is None:
            []
        else:
            return view.get_regions(f"tutkain_gutter_marks/{tag}")

    #@unittest.SkipTest
    def test_smoke_view(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        server = self.connect(window, {"dialect": "clj", "output": "view"})
        self.set_view_content(view, "(inc 1)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        self.eval_context(server.backchannel)
        self.assertEquals("(inc 1)\n", server.recv())
        server.send("2")
        output_view = state.get_active_connection(window, edn.Keyword("clj")).view

        yield lambda: self.equals(
            """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n""",
            self.content(output_view)
        )

        yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(output_view, "in")
        yield lambda: [sublime.Region(32, 32)] == self.gutter_marks(output_view, "ret")

        self.disconnect(window)
        self.assertEquals(":repl/quit\n", server.recv())
        self.close_window(window)
        server.backchannel.stop()
        server.stop()

    #@unittest.SkipTest
    def test_view_tap_panel_enabled(self):
        window = self.make_window()
        self.make_scratch_view(window)
        settings.load().set("tap_panel", True)
        server = self.connect(window, {"dialect": "clj", "output": "view"})
        server.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42"}))

        yield lambda: self.equals(
            """42""",
            self.content(window.find_output_panel("tutkain.tap_panel"))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit\n", server.recv())
        self.close_window(window)
        server.backchannel.stop()
        server.stop()

    #@unittest.SkipTest
    def test_view_tap_panel_disabled(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        settings.load().set("tap_panel", False)
        server = self.connect(window, {"dialect": "clj", "output": "view"})
        self.set_view_content(view, "(tap> 42)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        # FIXME: Newline after val
        server.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42"}))
        output_view = state.get_active_connection(window, edn.Keyword("clj")).view

        yield lambda: self.equals(
            """\u2063Clojure 1.11.0-alpha1\n\u2063(tap> 42)\n""",
            self.content(output_view)
        )

        yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(output_view, "in")

        yield lambda: self.equals(
            """""",
            self.content(window.find_output_panel("tutkain.tap_panel"))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit\n", server.recv())
        self.close_window(window)
        server.backchannel.stop()
        server.stop()

    #@unittest.SkipTest
    def test_panel_tap_panel_enabled(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        settings.load().set("tap_panel", True)
        server = self.connect(window, {"dialect": "clj", "output": "panel"})
        self.set_view_content(view, "(tap> 42)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        # FIXME: Newline after val
        server.send("true")
        server.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42\n"}))

        yield lambda: self.equals(
            """\u2063Clojure 1.11.0-alpha1\n\u2063(tap> 42)\ntrue\n42\n""",
            self.content(self.output_panel(window))
        ) or self.equals(
            """\u2063Clojure 1.11.0-alpha1\n\u2063(tap> 42)\42\ntrue\n""",
            self.content(self.output_panel(window))
        )

        yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(self.output_panel(window), "in")
        yield lambda: [sublime.Region(34, 34)] == self.gutter_marks(self.output_panel(window), "ret")
        yield lambda: [sublime.Region(39, 39)] == self.gutter_marks(self.output_panel(window), "tap")

        self.disconnect(window)
        self.assertEquals(":repl/quit\n", server.recv())
        self.close_window(window)
        server.backchannel.stop()
        server.stop()

    #@unittest.SkipTest
    def test_panel_tap_panel_disabled(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        settings.load().set("tap_panel", False)
        server = self.connect(window, {"dialect": "clj", "output": "panel"})
        self.set_view_content(view, "(tap> 42)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        server.send("true")
        server.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42\n"}))

        yield lambda: self.equals(
            """\u2063Clojure 1.11.0-alpha1\n\u2063(tap> 42)\ntrue\n""",
            self.content(self.output_panel(window))
        )

        yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(self.output_panel(window), "in")
        yield lambda: [sublime.Region(34, 34)] == self.gutter_marks(self.output_panel(window), "ret")

        self.disconnect(window)
        self.assertEquals(":repl/quit\n", server.recv())
        self.close_window(window)
        server.backchannel.stop()
        server.stop()

    #@unittest.SkipTest
    def test_smoke_panel(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        server = self.connect(window, {"dialect": "clj", "output": "panel"})
        self.set_view_content(view, "(inc 1)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        self.eval_context(server.backchannel)
        self.assertEquals("(inc 1)\n", server.recv())
        server.send("2")

        yield lambda: self.equals(
            """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n""",
            self.content(self.output_panel(window))
        )

        yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(self.output_panel(window), "in")
        yield lambda: [sublime.Region(32, 32)] == self.gutter_marks(self.output_panel(window), "ret")

        self.disconnect(window)
        self.assertEquals(":repl/quit\n", server.recv())
        self.close_window(window)
        server.backchannel.stop()
        server.stop()

    #@unittest.SkipTest
    def test_panel_multiple(self):
        if not sys.platform.startswith("win"):
            window = self.make_window()
            jvm_view = self.make_scratch_view(window)
            jvm_server = self.connect(window, {"dialect": "clj", "output": "panel"})

            self.set_view_content(jvm_view, "(inc 1)")
            self.set_selections(jvm_view, (0, 0))

            jvm_view.run_command("tutkain_evaluate")
            self.eval_context(jvm_server.backchannel)
            self.assertEquals("(inc 1)\n", jvm_server.recv())
            jvm_server.send("2")

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n""",
                self.content(self.output_panel(window))
            )

            yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(self.output_panel(window), "in")
            yield lambda: [sublime.Region(32, 32)] == self.gutter_marks(self.output_panel(window), "ret")

            js_view = self.make_scratch_view(window, "ClojureScript (Tutkain).sublime-syntax")
            js_server = self.connect(window, {"dialect": "cljs", "output": "panel", "build_id": "app"})

            self.set_view_content(js_view, """(js/parseInt "42")""")
            self.set_selections(js_view, (0, 0))

            js_view.run_command("tutkain_evaluate")
            self.eval_context(js_server.backchannel, ns=edn.Symbol("cljs.user"))
            self.assertEquals("""(js/parseInt "42")\n""", js_server.recv())
            js_server.send("42")

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n\u2063ClojureScript 1.10.844\n\u2063(js/parseInt "42")\n42\n""",
                self.content(self.output_panel(window))
            )

            yield lambda: [
                sublime.Region(24, 24),
                sublime.Region(59, 59)
            ] == self.gutter_marks(self.output_panel(window), "in")

            yield lambda: [
                sublime.Region(32, 32),
                sublime.Region(78, 78)
            ] == self.gutter_marks(self.output_panel(window), "ret")

            self.disconnect(window)
            yield unittesting.AWAIT_WORKER
            jvm_view.window().run_command("select")
            yield
            self.assertEquals(":repl/quit\n", jvm_server.recv())
            self.disconnect(window)
            yield unittesting.AWAIT_WORKER
            jvm_view.window().run_command("select")
            yield
            self.assertEquals(":repl/quit\n", js_server.recv())
            self.close_window(window)
            jvm_server.backchannel.stop()
            jvm_server.stop()
            js_server.backchannel.stop()
            js_server.stop()

    #@unittest.SkipTest
    def test_panel_multiple_same_runtime(self):
        if not sys.platform.startswith("win"):
            window = self.make_window()
            jvm_view_1 = self.make_scratch_view(window)
            jvm_1_server = self.connect(window, {"dialect": "clj", "output": "panel"})

            self.set_view_content(jvm_view_1, "(inc 1)")
            self.set_selections(jvm_view_1, (0, 0))

            jvm_view_1.run_command("tutkain_evaluate")
            self.eval_context(jvm_1_server.backchannel)
            self.assertEquals("(inc 1)\n", jvm_1_server.recv())
            jvm_1_server.send("2")

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n""",
                self.content(self.output_panel(window))
            )

            yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(self.output_panel(window), "in")
            yield lambda: [sublime.Region(32, 32)] == self.gutter_marks(self.output_panel(window), "ret")

            jvm_view_2 = self.make_scratch_view(window)
            jvm_2_server = self.connect(window, {"dialect": "clj", "output": "panel"})

            self.set_view_content(jvm_view_2, """(inc 2)""")
            self.set_selections(jvm_view_2, (0, 0))

            jvm_view_2.run_command("tutkain_evaluate")
            self.eval_context(jvm_2_server.backchannel)
            self.assertEquals("""(inc 2)\n""", jvm_2_server.recv())
            jvm_2_server.send("3")

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n\u2063Clojure 1.11.0-alpha1\n\u2063(inc 2)\n3\n""",
                self.content(self.output_panel(window))
            )

            yield lambda: [
                sublime.Region(24, 24),
                sublime.Region(58, 58)
            ] == self.gutter_marks(self.output_panel(window), "in")

            yield lambda: [
                sublime.Region(32, 32),
                sublime.Region(66, 66)
            ] == self.gutter_marks(self.output_panel(window), "ret")

            self.disconnect(window)

            yield unittesting.AWAIT_WORKER
            jvm_view_1.window().run_command("select")
            yield

            self.assertEquals(":repl/quit\n", jvm_1_server.recv())

            self.set_view_content(jvm_view_2, "(inc 3)")
            self.set_selections(jvm_view_2, (0, 0))

            jvm_view_2.run_command("tutkain_evaluate")
            self.eval_context(jvm_2_server.backchannel)
            self.assertEquals("(inc 3)\n", jvm_2_server.recv())
            jvm_2_server.send("4")

            yield lambda: self.equals(
                f"""\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n\u2063Clojure 1.11.0-alpha1\n\u2063(inc 2)\n3\n\u2063\u2063[Tutkain] Disconnected from Clojure runtime at {jvm_1_server.host}:{jvm_1_server.port}.\n\u2063\u2063(inc 3)\n4\n""",
                self.content(state.get_active_connection(window, edn.Keyword("clj")).view)
            ) or self.equals(
                f"""\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n\u2063Clojure 1.11.0-alpha1\n\u2063(inc 2)\n3\n(inc 3)\n\u2063\u2063[Tutkain] Disconnected from Clojure runtime at {jvm_1_server.host}:{jvm_1_server.port}.\n\u2063\u20634\n""",
                self.content(state.get_active_connection(window, edn.Keyword("clj")).view)
            )

            yield lambda: [
                sublime.Region(24, 24),
                sublime.Region(58, 58),
                sublime.Region(136, 136),
            ] == self.gutter_marks(self.output_panel(window), "in")

            yield lambda: [
                sublime.Region(32, 32),
                sublime.Region(66, 66),
                sublime.Region(144, 144)
            ] == self.gutter_marks(self.output_panel(window), "ret")

            self.disconnect(window)
            jvm_view_2.window().run_command("select")
            self.assertEquals(":repl/quit\n", jvm_2_server.recv())
            self.close_window(window)
            jvm_1_server.stop()
            jvm_1_server.backchannel.stop()
            jvm_2_server.stop()
            jvm_2_server.backchannel.stop()

    #@unittest.SkipTest
    def test_view_multiple(self):
        if not sys.platform.startswith("win"):
            window = self.make_window()
            jvm_view = self.make_scratch_view(window)
            jvm_server = self.connect(window, {"dialect": "clj", "output": "view"})

            self.set_view_content(jvm_view, "(inc 1)")
            self.set_selections(jvm_view, (0, 0))

            jvm_view.run_command("tutkain_evaluate")
            self.eval_context(jvm_server.backchannel)
            self.assertEquals("(inc 1)\n", jvm_server.recv())
            jvm_server.send("2")
            output_view = state.get_active_connection(window, edn.Keyword("clj")).view

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n""",
                self.content(output_view)
            )

            yield lambda: [sublime.Region(24, 24)] == self.gutter_marks(output_view, "in")
            yield lambda: [sublime.Region(32, 32)] == self.gutter_marks(output_view, "ret")

            js_view = self.make_scratch_view(window, "ClojureScript (Tutkain).sublime-syntax")
            js_server = self.connect(window, {"dialect": "cljs", "output": "view", "build_id": "app"})

            self.set_view_content(js_view, """(js/parseInt "42")""")
            self.set_selections(js_view, (0, 0))

            js_view.run_command("tutkain_evaluate")
            self.eval_context(js_server.backchannel, ns=edn.Symbol("cljs.user"))
            self.assertEquals("""(js/parseInt "42")\n""", js_server.recv())
            js_server.send("42")
            output_view = state.get_active_connection(window, edn.Keyword("cljs")).view

            yield lambda: self.equals(
                """\u2063ClojureScript 1.10.844\n\u2063(js/parseInt "42")\n42\n""",
                self.content(output_view)
            )

            yield lambda: [sublime.Region(25, 25)] == self.gutter_marks(output_view, "in")
            yield lambda: [sublime.Region(44, 44)] == self.gutter_marks(output_view, "ret")

            self.disconnect(window)
            # Move down to select ClojureScript runtime

            yield unittesting.AWAIT_WORKER
            js_view.window().run_command("move", {"by": "lines", "forward": True})
            js_view.window().run_command("select")
            yield

            self.assertEquals(":repl/quit\n", js_server.recv())

            self.set_view_content(jvm_view, "(inc 2)")
            self.set_selections(jvm_view, (0, 0))

            jvm_view.run_command("tutkain_evaluate")
            self.eval_context(jvm_server.backchannel)
            self.assertEquals("(inc 2)\n", jvm_server.recv())
            jvm_server.send("3")
            output_view = state.get_active_connection(window, edn.Keyword("clj")).view

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n(inc 2)\n3\n""",
                self.content(output_view)
            )

            yield lambda: [
                sublime.Region(24, 24),
                sublime.Region(34, 34)
            ] == self.gutter_marks(output_view, "in")

            yield lambda: [
                sublime.Region(32, 32),
                sublime.Region(42, 42)
            ] == self.gutter_marks(output_view, "ret")

            self.disconnect(window)
            # Don't need to select because there's only one remaining runtime
            self.assertEquals(":repl/quit\n", jvm_server.recv())
            self.close_window(window)
            jvm_server.backchannel.stop()
            jvm_server.stop()
            js_server.backchannel.stop()
            js_server.stop()

    #@unittest.SkipTest
    def test_panel_and_view(self):
        if not sys.platform.startswith("win"):
            window = self.make_window()
            jvm_view = self.make_scratch_view(window)
            jvm_server = self.connect(window, {"dialect": "clj", "output": "panel"})

            self.set_view_content(jvm_view, "(inc 1)")
            self.set_selections(jvm_view, (0, 0))

            jvm_view.run_command("tutkain_evaluate")
            self.eval_context(jvm_server.backchannel)
            self.assertEquals("(inc 1)\n", jvm_server.recv())
            jvm_server.send("2")

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n""",
                self.content(self.output_panel(window))
            )

            js_view = self.make_scratch_view(window, "ClojureScript (Tutkain).sublime-syntax")
            js_server = self.connect(window, {"dialect": "cljs", "output": "view", "build_id": "app"})

            self.set_view_content(js_view, """(js/parseInt "42")""")
            self.set_selections(js_view, (0, 0))

            js_view.run_command("tutkain_evaluate")
            self.eval_context(js_server.backchannel, ns=edn.Symbol("cljs.user"))
            self.assertEquals("""(js/parseInt "42")\n""", js_server.recv())
            js_server.send("42")
            output_view = state.get_active_connection(window, edn.Keyword("cljs")).view

            yield lambda: self.equals(
                """\u2063ClojureScript 1.10.844\n\u2063(js/parseInt "42")\n42\n""",
                self.content(output_view)
            )

            yield lambda: [sublime.Region(25, 25)] == self.gutter_marks(output_view, "in")
            yield lambda: [sublime.Region(44, 44)] == self.gutter_marks(output_view, "ret")

            self.disconnect(window)

            # Move down to select ClojureScript runtime
            yield unittesting.AWAIT_WORKER
            js_view.window().run_command("move", {"by": "lines", "forward": True})
            js_view.window().run_command("select")
            yield

            self.assertEquals(":repl/quit\n", js_server.recv())

            self.set_view_content(jvm_view, "(inc 2)")
            self.set_selections(jvm_view, (0, 0))

            jvm_view.run_command("tutkain_evaluate")
            self.eval_context(jvm_server.backchannel)
            self.assertEquals("(inc 2)\n", jvm_server.recv())
            jvm_server.send("3")

            yield lambda: self.equals(
                """\u2063Clojure 1.11.0-alpha1\n\u2063(inc 1)\n2\n(inc 2)\n3\n""",
                self.content(state.get_active_connection(window, edn.Keyword("clj")).view)
            )

            self.disconnect(window)
            # Don't need to select because there's only one remaining runtime
            self.assertEquals(":repl/quit\n", jvm_server.recv())
            self.close_window(window)
            jvm_server.backchannel.stop()
            jvm_server.stop()
            js_server.backchannel.stop()
            js_server.stop()

    #@unittest.SkipTest
    def test_no_backchannel(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        server = self.connect(window, {"dialect": "clj", "backchannel": False})
        self.assertFalse(hasattr(server, "backchannel"))

        yield lambda: self.equals(
            """user=> """,
            self.content(state.get_active_connection(window, edn.Keyword("clj")).view)
        )

        self.set_view_content(view, "(inc 1)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        self.assertEquals("(inc 1)\n", server.recv())

        yield lambda: self.equals(
            """user=> (inc 1)\n""",
            self.content(state.get_active_connection(window, edn.Keyword("clj")).view)
        )

        server.send("2")

        yield lambda: self.equals(
            """user=> (inc 1)\n2\n""",
            self.content(state.get_active_connection(window, edn.Keyword("clj")).view)
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit\n", server.recv())
        self.close_window(window)
        server.stop()
