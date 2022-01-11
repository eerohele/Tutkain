import sublime

from Tutkain.src import repl
from Tutkain.src.repl import formatter

from .mock import REPL
from .util import PackageTestCase


class TestBabashkaClient(PackageTestCase):
    def get_print(self):
        return self.client.printq.get(timeout=5)

    @classmethod
    def setUpClass(self):
        super().setUpClass()

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

        self.window = sublime.active_window()
        self.server = REPL(greeting=write_greeting).start()
        self.client = repl.BabashkaClient(self.server.host, self.server.port)
        self.output_view = repl.views.get_or_create_view(self.window, "view")
        repl.start(self.output_view, self.client)
        self.client.printq.get(timeout=1)

        self.addClassCleanup(repl.stop, self.window)
        self.addClassCleanup(self.server.stop)

    def setUp(self):
        super().setUp(syntax="Babashka (Tutkain).sublime-syntax")

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.assertEquals("(range 10)\n", self.server.recv())
        self.assertEquals(formatter.value("(range 10)\n"), self.get_print())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals(formatter.value("(0 1 2 3 4 5 6 7 8 9)\n"), self.get_print())
