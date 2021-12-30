from .mock import Server, send_edn, send_text
from Tutkain.api import edn
from Tutkain.src import repl
from Tutkain.src import settings
from Tutkain.src import state

import sublime
import textwrap
import time
import types
import unittest


class TestCase(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.original_settings = settings.load().to_dict()

    def tearDown(self):
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


def clojure_handshake(server):
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
        server.send(f"""{{:greeting "Clojure 1.11.0-alpha1\\n" :host "localhost", :port {backchannel.port}}}""")

        # Client loads modules
        for _ in range(8):
            module = edn.read(backchannel.recv())

            backchannel.send(edn.kwmap({
                "id": module.get(edn.Keyword("id")),
                "result": edn.Keyword("ok"),
                "filename": module.get(edn.Keyword("filename"))
            }))

        return backchannel


def clojurescript_handshake(server):
    # Client starts clojure.main/repl
    server.recv()

    # Client requests build IDs
    server.recv()

    # Server sends build ID list
    server.send("[:browser, :node-script, :npm]")

    # Client selects the first build ID
    sublime.active_window().run_command("select")

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
        server.send(f"""{{:greeting "ClojureScript 1.10.844\\n" :host "localhost", :port {backchannel.port}}}""")

        for _ in range(8):
            backchannel.recv()

        return backchannel


class TestConnectDisconnect(TestCase):
    def run_connect_command(self, window, args):
        window.run_command("tutkain_connect", args)

    def connect(self, window, args):
        def write_greeting(buf):
            buf.write("user=> ")
            buf.flush()

        server = Server(send_text, greeting=write_greeting).start()
        default_args = {"host": server.host, "port": server.port}

        if args.get("backchannel", True):
            sublime.set_timeout_async(lambda: self.run_connect_command(window, {**default_args, **args}), 0)
        else:
            self.run_connect_command(window, {**default_args, **args})

        dialect = args.get("dialect", "clj")

        if args.get("backchannel", True):
            if dialect == "clj":
                backchannel = clojure_handshake(server)
            elif dialect == "cljs":
                backchannel = clojurescript_handshake(server)
        else:
            backchannel = None

        return types.SimpleNamespace(server=server, backchannel=backchannel)

    def disconnect(self, window):
        window.run_command("tutkain_disconnect")

    def eval_context(self, backchannel, file="NO_SOURCE_FILE", line=1, column=1):
        actual = edn.read(backchannel.recv())
        id = actual.get(edn.Keyword("id"))

        response = edn.kwmap({
             "id": id,
             "op": edn.Keyword("set-eval-context"),
             "file": file,
             "line": line,
             "column": column,
        })

        self.assertEquals(response, actual)

        backchannel.send(edn.kwmap({
            "id": id,
            "file": file
        }))

    def output_panel(self, window):
        return window.find_output_panel(repl.views.output_panel_name())

    def wait_until_equals(self, expected, actual, sleep=0.1, tryNumber=0, tries=10):
        if self.dedent(expected) != (a := actual()):
            if tryNumber == tries:
                if a is not None:
                    raise AssertionError(f"Expected {self.dedent(expected).encode()}, got {a.encode()}")
                else:
                    raise AssertionError("Actual was None")

            time.sleep(sleep)
            self.wait_until_equals(expected, actual, tryNumber=tryNumber + 1, tries=tries)

    def dedent(self, string):
        if string and string[0] == "\n":
            string = string[1:]

        return textwrap.dedent(string)

    def test_smoke_view(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        connection = self.connect(window, {"dialect": "clj", "output": "view"})
        self.set_view_content(view, "(inc 1)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        self.eval_context(connection.backchannel)
        self.assertEquals("(inc 1)\n", connection.server.recv())
        connection.server.send("user=> (inc 1)")
        connection.server.send("2")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            """, lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit", connection.server.recv())
        self.close_window(window)

    def test_view_tap_panel_enabled(self):
        window = self.make_window()
        self.make_scratch_view(window)
        settings.load().set("tap_panel", True)
        connection = self.connect(window, {"dialect": "clj", "output": "view"})
        connection.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42"}))

        self.wait_until_equals(
            """42""",
            lambda: self.content(window.find_output_panel("tutkain.tap_panel"))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit", connection.server.recv())
        self.close_window(window)

    def test_view_tap_panel_disabled(self):
        window = self.make_window()
        self.make_scratch_view(window)
        settings.load().set("tap_panel", False)
        connection = self.connect(window, {"dialect": "clj", "output": "view"})
        connection.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42"}))

        # TODO: Flaky
        time.sleep(1)

        self.assertEquals(
            """""",
            self.content(window.find_output_panel("tutkain.tap_panel"))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit", connection.server.recv())
        self.close_window(window)

    def test_panel_tap_panel_enabled(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        settings.load().set("tap_panel", True)
        connection = self.connect(window, {"dialect": "clj", "output": "panel"})
        self.set_view_content(view, "(tap> 42)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        connection.server.send("user=> true")
        # FIXME: Newline after val
        connection.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42"}))

        try:
            self.wait_until_equals(
                """
                Clojure 1.11.0-alpha1
                user=> true
                42""", lambda: self.content(self.output_panel(window))
            )
        except AssertionError:
            self.wait_until_equals(
                """
                Clojure 1.11.0-alpha1
                42user=> true
                """, lambda: self.content(self.output_panel(window))
            )

        self.disconnect(window)
        self.assertEquals(":repl/quit", connection.server.recv())
        self.close_window(window)

    def test_panel_tap_panel_disabled(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        settings.load().set("tap_panel", False)
        connection = self.connect(window, {"dialect": "clj", "output": "panel"})
        self.set_view_content(view, "(tap> 42)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        connection.server.send("user=> true")
        connection.backchannel.send(edn.kwmap({"tag": edn.Keyword("tap"), "val": "42"}))

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> true
            """, lambda: self.content(self.output_panel(window))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit", connection.server.recv())
        self.close_window(window)

    def test_smoke_panel(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        connection = self.connect(window, {"dialect": "clj", "output": "panel"})
        self.set_view_content(view, "(inc 1)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        self.eval_context(connection.backchannel)
        self.assertEquals("(inc 1)\n", connection.server.recv())
        connection.server.send("user=> (inc 1)")
        connection.server.send("2")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            """, lambda: self.content(self.output_panel(window))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit", connection.server.recv())
        self.close_window(window)

    def test_panel_multiple(self):
        window = self.make_window()
        jvm_view = self.make_scratch_view(window)
        jvm = self.connect(window, {"dialect": "clj", "output": "panel"})

        self.set_view_content(jvm_view, "(inc 1)")
        self.set_selections(jvm_view, (0, 0))

        jvm_view.run_command("tutkain_evaluate")
        self.eval_context(jvm.backchannel)
        self.assertEquals("(inc 1)\n", jvm.server.recv())
        jvm.server.send("user=> (inc 1)")
        jvm.server.send("2")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            """, lambda: self.content(self.output_panel(window))
        )

        js_view = self.make_scratch_view(window, "ClojureScript (Tutkain).sublime-syntax")
        js = self.connect(window, {"dialect": "cljs", "output": "panel"})

        self.set_view_content(js_view, """(js/parseInt "42")""")
        self.set_selections(js_view, (0, 0))

        js_view.run_command("tutkain_evaluate")
        self.eval_context(js.backchannel)
        self.assertEquals("""(js/parseInt "42")\n""", js.server.recv())
        js.server.send("""cljs.user=> (js/parseInt "42")""")
        js.server.send("42")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            ClojureScript 1.10.844
            cljs.user=> (js/parseInt "42")
            42
            """, lambda: self.content(self.output_panel(window))
        )

        self.disconnect(window)
        jvm_view.window().run_command("select")
        self.assertEquals(":repl/quit", jvm.server.recv())
        self.disconnect(window)
        js_view.window().run_command("select")
        self.assertEquals(":repl/quit", js.server.recv())
        self.close_window(window)

    # def test_panel_multiple_same_runtime(self):
    #     window = self.make_window()
    #     jvm_view_1 = self.make_scratch_view(window)
    #     jvm_1 = self.connect(window, {"dialect": "clj", "output": "panel"})

    #     self.set_view_content(jvm_view_1, "(inc 1)")
    #     self.set_selections(jvm_view_1, (0, 0))

    #     jvm_view_1.run_command("tutkain_evaluate")
    #     self.eval_context(jvm_1.backchannel)
    #     self.assertEquals("(inc 1)\n", jvm_1.server.recv())
    #     jvm_1.server.send("user=> (inc 1)")
    #     jvm_1.server.send("2")

    #     self.wait_until_equals(
    #         """
    #         Clojure 1.11.0-alpha1
    #         user=> (inc 1)
    #         2
    #         """, lambda: self.content(self.output_panel(window))
    #     )

    #     jvm_view_2 = self.make_scratch_view(window)
    #     jvm_2 = self.connect(window, {"dialect": "clj", "output": "panel"})

    #     self.set_view_content(jvm_view_2, """(inc 2)""")
    #     self.set_selections(jvm_view_2, (0, 0))

    #     jvm_view_2.run_command("tutkain_evaluate")
    #     self.eval_context(jvm_2.backchannel)
    #     self.assertEquals("""(inc 2)\n""", jvm_2.server.recv())
    #     jvm_2.server.send("""user=> (inc 2)""")
    #     jvm_2.server.send("3")

    #     self.wait_until_equals(
    #         """
    #         Clojure 1.11.0-alpha1
    #         user=> (inc 1)
    #         2
    #         Clojure 1.11.0-alpha1
    #         user=> (inc 2)
    #         3
    #         """, lambda: self.content(self.output_panel(window))
    #     )

    #     self.disconnect(window)
    #     jvm_view_1.window().run_command("select")
    #     self.assertEquals(":repl/quit", jvm_1.server.recv())

    #     self.set_view_content(jvm_view_2, "(inc 3)")
    #     self.set_selections(jvm_view_2, (0, 0))

    #     jvm_view_2.run_command("tutkain_evaluate")
    #     self.eval_context(jvm_2.backchannel)
    #     self.assertEquals("(inc 3)\n", jvm_2.server.recv())
    #     jvm_2.server.send("user=> (inc 3)")
    #     jvm_2.server.send("4")

    #     self.wait_until_equals(
    #         # YO! This string has invisible unicode characters as per REPL (Tutkain).sublime-syntax.
    #         f"""
    #         Clojure 1.11.0-alpha1
    #         user=> (inc 1)
    #         2
    #         Clojure 1.11.0-alpha1
    #         user=> (inc 2)
    #         3
    #         ⁣⁣[Tutkain] Disconnected from Clojure runtime at {jvm_1.server.host}:{jvm_1.server.port}.
    #         ⁣⁣user=> (inc 3)
    #         4
    #         """, lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
    #     )

    #     self.disconnect(window)
    #     jvm_view_2.window().run_command("select")
    #     self.assertEquals(":repl/quit", jvm_2.server.recv())
    #     self.close_window(window)

    def test_view_multiple(self):
        window = self.make_window()
        jvm_view = self.make_scratch_view(window)
        jvm = self.connect(window, {"dialect": "clj", "output": "view"})

        self.set_view_content(jvm_view, "(inc 1)")
        self.set_selections(jvm_view, (0, 0))

        jvm_view.run_command("tutkain_evaluate")
        self.eval_context(jvm.backchannel)
        self.assertEquals("(inc 1)\n", jvm.server.recv())
        jvm.server.send("user=> (inc 1)")
        jvm.server.send("2")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            """, lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
        )

        js_view = self.make_scratch_view(window, "ClojureScript (Tutkain).sublime-syntax")
        js = self.connect(window, {"dialect": "cljs", "output": "view"})

        self.set_view_content(js_view, """(js/parseInt "42")""")
        self.set_selections(js_view, (0, 0))

        js_view.run_command("tutkain_evaluate")
        self.eval_context(js.backchannel)
        self.assertEquals("""(js/parseInt "42")\n""", js.server.recv())
        js.server.send("""cljs.user=> (js/parseInt "42")""")
        js.server.send("42")

        self.wait_until_equals(
            """
            ClojureScript 1.10.844
            cljs.user=> (js/parseInt "42")
            42
            """, lambda: self.content(state.get_active_connection_view(edn.Keyword("cljs")))
        )

        self.disconnect(window)
        # Move down to select ClojureScript runtime
        js_view.window().run_command("move", {"by": "lines", "forward": True})
        js_view.window().run_command("select")
        self.assertEquals(":repl/quit", js.server.recv())

        self.set_view_content(jvm_view, "(inc 2)")
        self.set_selections(jvm_view, (0, 0))

        jvm_view.run_command("tutkain_evaluate")
        self.eval_context(jvm.backchannel)
        self.assertEquals("(inc 2)\n", jvm.server.recv())
        jvm.server.send("user=> (inc 2)")
        jvm.server.send("3")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            user=> (inc 2)
            3
            """, lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
        )

        self.disconnect(window)
        # Don't need to select because there's only one remaining runtime
        self.assertEquals(":repl/quit", jvm.server.recv())
        self.close_window(window)

    def test_panel_and_view(self):
        window = self.make_window()
        jvm_view = self.make_scratch_view(window)
        jvm = self.connect(window, {"dialect": "clj", "output": "panel"})

        self.set_view_content(jvm_view, "(inc 1)")
        self.set_selections(jvm_view, (0, 0))

        jvm_view.run_command("tutkain_evaluate")
        self.eval_context(jvm.backchannel)
        self.assertEquals("(inc 1)\n", jvm.server.recv())
        jvm.server.send("user=> (inc 1)")
        jvm.server.send("2")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            """, lambda: self.content(self.output_panel(window))
        )

        js_view = self.make_scratch_view(window, "ClojureScript (Tutkain).sublime-syntax")
        js = self.connect(window, {"dialect": "cljs", "output": "view"})

        self.set_view_content(js_view, """(js/parseInt "42")""")
        self.set_selections(js_view, (0, 0))

        js_view.run_command("tutkain_evaluate")
        self.eval_context(js.backchannel)
        self.assertEquals("""(js/parseInt "42")\n""", js.server.recv())
        js.server.send("""cljs.user=> (js/parseInt "42")""")
        js.server.send("42")

        self.wait_until_equals(
            """
            ClojureScript 1.10.844
            cljs.user=> (js/parseInt "42")
            42
            """, lambda: self.content(state.get_active_connection_view(edn.Keyword("cljs")))
        )

        self.disconnect(window)
        # Move down to select ClojureScript runtime
        js_view.window().run_command("move", {"by": "lines", "forward": True})
        js_view.window().run_command("select")
        self.assertEquals(":repl/quit", js.server.recv())

        self.set_view_content(jvm_view, "(inc 2)")
        self.set_selections(jvm_view, (0, 0))

        jvm_view.run_command("tutkain_evaluate")
        self.eval_context(jvm.backchannel)
        self.assertEquals("(inc 2)\n", jvm.server.recv())
        jvm.server.send("user=> (inc 2)")
        jvm.server.send("3")

        self.wait_until_equals(
            """
            Clojure 1.11.0-alpha1
            user=> (inc 1)
            2
            user=> (inc 2)
            3
            """, lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
        )

        self.disconnect(window)
        # Don't need to select because there's only one remaining runtime
        self.assertEquals(":repl/quit", jvm.server.recv())
        self.close_window(window)

    def test_no_backchannel(self):
        window = self.make_window()
        view = self.make_scratch_view(window)
        connection = self.connect(window, {"dialect": "clj", "backchannel": False})

        self.wait_until_equals(
            """user=> """,
            lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
        )

        self.set_view_content(view, "(inc 1)")
        self.set_selections(view, (0, 0))
        view.run_command("tutkain_evaluate")
        self.assertEquals("(inc 1)\n", connection.server.recv())

        self.wait_until_equals(
            """user=> (inc 1)\n""",
            lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
        )

        connection.server.send("2")

        self.wait_until_equals(
            """
            user=> (inc 1)
            2
            """, lambda: self.content(state.get_active_connection_view(edn.Keyword("clj")))
        )

        self.disconnect(window)
        self.assertEquals(":repl/quit", connection.server.recv())
        self.close_window(window)
