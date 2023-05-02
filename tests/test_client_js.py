import sublime

from Tutkain.api import edn
from Tutkain.src import repl

from .mock import JsServer
from .util import PackageTestCase


def input(val):
    return edn.kwmap({"tag": edn.Keyword("in"), "val": val})


class TestJSClient(PackageTestCase):
    def get_print(self):
        return self.client.printq.get(timeout=5)

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.window = sublime.active_window()
        server = JsServer().start()
        self.client = repl.JSClient(
            server.host, server.port, options={"build_id": edn.Keyword("app")}
        )
        self.output_view = repl.views.get_or_create_view(self.window, "view")
        repl.start(self.output_view, self.client)
        self.server = server.connection.result(timeout=5)
        self.client.printq.get(timeout=5)

        self.addClassCleanup(repl.stop, self.window)
        self.addClassCleanup(self.server.stop)

    def setUp(self):
        super().setUp(syntax="Packages/Tutkain/ClojureScript (Tutkain).sublime-syntax")

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals(input("(range 10)\n"), self.get_print())
        self.assertEquals(
            edn.kwmap(
                {
                    "op": edn.Keyword("eval"),
                    "dialect": edn.Keyword("cljs"),
                    "code": "(range 10)",
                    "file": "NO_SOURCE_FILE",
                    "ns": edn.Symbol("cljs.user"),
                    "line": 1,
                    "column": 10,
                    "id": 9,
                }
            ),
            edn.read(self.server.recv()),
        )
        self.server.send(
            edn.kwmap(
                {"id": 9, "tag": edn.Keyword("ret"), "val": "(0 1 2 3 4 5 6 7 8 9)\n"}
            )
        )

        self.assertEquals(
            edn.kwmap(
                {"id": 9, "tag": edn.Keyword("ret"), "val": "(0 1 2 3 4 5 6 7 8 9)\n"}
            ),
            self.get_print(),
        )
