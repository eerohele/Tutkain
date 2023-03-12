import sublime

from Tutkain.api import edn
from Tutkain.src import repl
from Tutkain.src.repl import formatter

from .mock import BabashkaServer
from .util import PackageTestCase


def input(val):
    return edn.kwmap({"tag": edn.Keyword("in"), "val": val})


def ret(val):
    return edn.kwmap({"tag": edn.Keyword("ret"), "val": val})


class TestBabashkaClient(PackageTestCase):
    def get_print(self):
        return self.client.printq.get(timeout=5)

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.window = sublime.active_window()
        server = BabashkaServer().start()
        self.client = repl.BabashkaClient(server.host, server.port, "repl")
        self.output_view = repl.views.get_or_create_view(self.window, "view")
        repl.start(self.output_view, self.client)
        self.server = server.connection.result(timeout=5)
        self.client.printq.get(timeout=5)

        self.addClassCleanup(repl.stop, self.window)
        self.addClassCleanup(self.server.backchannel.stop)
        self.addClassCleanup(self.server.stop)

    def setUp(self):
        super().setUp(syntax="Packages/Tutkain/Babashka (Tutkain).sublime-syntax")

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals(input("(range 10)\n"), self.get_print())
        self.eval_context(column=10)
        self.assertEquals("(range 10)\n", self.server.recv())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals(ret("(0 1 2 3 4 5 6 7 8 9)\n"), self.get_print())
