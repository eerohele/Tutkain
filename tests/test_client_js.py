import sublime
import queue

from Tutkain.api import edn
from Tutkain.package import start_logging, stop_logging
from Tutkain.src import repl
from Tutkain.src.repl import views
from Tutkain.src import state

from .mock import Server, send_edn, send_text
from .util import PackageTestCase


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

            for _ in range(8):
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
            self.server.host,
            self.server.port,
            lambda _, on_done: on_done(1)
        )

        self.server.executor.submit(self.client.connect)

        dialect = edn.Keyword("cljs")
        self.repl_view = sublime.active_window().new_file()
        views.configure(self.repl_view, dialect, "1", self.client.host, self.client.port)
        state.register_connection(self.repl_view, dialect, self.client)
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
        self.eval_context(column=10)
        self.assertEquals("(range 10)\n", self.server.recv())
        self.server.send("""user=> (range 10)""")
        self.assertEquals("user=> (range 10)\n", self.get_print())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals("(0 1 2 3 4 5 6 7 8 9)\n", self.get_print())
