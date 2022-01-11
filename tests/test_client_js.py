import sublime

from Tutkain.api import edn
from Tutkain.src import repl
from Tutkain.src.repl import formatter

from .mock import REPL, Backchannel
from .util import PackageTestCase


def conduct_handshake(server, client):
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
    server.send("#'tutkain.format/pp-str")
    server.recv()
    server.send("#'tutkain.backchannel/open")
    server.recv()
    server.send("""#object[clojure.lang.MultiFn 0x7fb5c837 "clojure.lang.MultiFn@7fb5c837"]""")
    server.recv()
    server.send("#'tutkain.repl/repl")

    # Client starts REPL
    server.recv()

    backchannel = Backchannel().start()

    server.send(f"""{{:greeting "ClojureScript 1.10.844\\n" :host "localhost", :port {backchannel.port}}}""")

    for _ in range(8):
        module = edn.read(backchannel.recv())

        backchannel.send(edn.kwmap({
            "id": module.get(edn.Keyword("id")),
            "result": edn.Keyword("ok"),
            "filename": module.get(edn.Keyword("filename"))
        }))

    # TODO: Add test for no runtime

    # ClojureScript version info is printed on the client
    client.printq.get(timeout=5)
    return backchannel


class TestJSClient(PackageTestCase):
    def get_print(self):
        return self.client.printq.get(timeout=5)

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        def write_greeting(buf):
            buf.write("shadow-cljs - REPL - see (help)\n")
            buf.flush()
            buf.write("To quit, type: :repl/quit\n")
            buf.flush()
            buf.write("shadow.user=> ")
            buf.flush()

        self.window = sublime.active_window()
        self.server = REPL(greeting=write_greeting).start()
        self.client = repl.JSClient(self.server.host, self.server.port, options={"build_id": edn.Keyword("app")})
        self.output_view = repl.views.get_or_create_view(self.window, "view")
        handshake = self.executor.submit(conduct_handshake, self.server, self.client)
        repl.start(self.output_view, self.client)
        self.backchannel = handshake.result()

        self.addClassCleanup(repl.stop, self.window)
        self.addClassCleanup(self.backchannel.stop)
        self.addClassCleanup(self.server.stop)

    def setUp(self):
        super().setUp(syntax="ClojureScript (Tutkain).sublime-syntax")

    def test_innermost(self):
        self.set_view_content("(map inc (range 10))")
        self.set_selections((9, 9))
        self.view.run_command("tutkain_evaluate", {"scope": "innermost"})
        self.eval_context(column=10)
        self.assertEquals("(range 10)\n", self.server.recv())
        self.server.send("""user=> (range 10)""")
        self.assertEquals(formatter.value("user=> (range 10)\n"), self.get_print())
        self.server.send("(0 1 2 3 4 5 6 7 8 9)")
        self.assertEquals(formatter.value("(0 1 2 3 4 5 6 7 8 9)\n"), self.get_print())
