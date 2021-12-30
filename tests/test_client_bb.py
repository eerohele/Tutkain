import sublime
import queue

from Tutkain.api import edn
from Tutkain.package import start_logging, stop_logging
from Tutkain.src import repl
from Tutkain.src.repl import views
from Tutkain.src import state

from .mock import Server, send_text
from .util import PackageTestCase


class TestBabashkaClient(PackageTestCase):
    def get_print(self):
        return self.client.printq.get(timeout=5)

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

        self.client = repl.BabashkaClient(self.server.host, self.server.port)
        self.server.executor.submit(self.client.connect)
        self.client.printq.get(timeout=1)
        dialect = edn.Keyword("bb")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, "1", self.client.host, self.client.port)
        state.register_connection(self.repl_view, dialect, self.client)

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
        self.assertEquals("(range 10)\n", self.get_print())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals("(0 1 2 3 4 5 6 7 8 9)\n", self.get_print())
