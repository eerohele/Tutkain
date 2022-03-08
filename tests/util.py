import sublime
import socket

from concurrent import futures
from threading import Event, Thread

from unittest import TestCase
from unittesting import DeferrableTestCase

from Tutkain.api import edn
from Tutkain.src import settings


class ViewTestCase(TestCase):
    @classmethod
    def setUpClass(self, syntax="Clojure (Tutkain).sublime-syntax"):
        sublime.run_command("new_window")
        self.view = sublime.active_window().new_file()
        self.view.set_name("tutkain.clj")
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.assign_syntax(syntax)
        settings.load().set("highlight_locals", False)

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command("close_window")

    def setUp(self):
        self.clear_view()

    def content(self, view):
        return view and view.substr(sublime.Region(0, view.size()))

    def view_content(self):
        return self.content(self.view)

    def clear_view(self):
        self.view.run_command("select_all")
        self.view.run_command("right_delete")

    def set_view_content(self, chars):
        self.clear_view()
        self.view.run_command("append", {"characters": chars})

    def set_selections(self, *pairs):
        self.view.sel().clear()

        for begin, end in pairs:
            self.view.sel().add(sublime.Region(begin, end))

    def selections(self):
        return [(region.begin(), region.end()) for region in self.view.sel()]

    def selection(self, i):
        return self.view.substr(self.view.sel()[i])


def echo_loop(server, stop_event):
    conn, _ = server.accept()

    while not stop_event.is_set():
        data = conn.recv(1024)
        conn.sendall(data)


def start_server():
    stop_event = Event()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", 0))
    server.listen(1)

    serve_loop = Thread(
        daemon=True,
        target=echo_loop,
        args=(
            server,
            stop_event,
        ),
    )

    serve_loop.name = "tutkain.test.serve_loop"
    serve_loop.start()
    return server, stop_event


def start_client(server):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(server.getsockname())
    client.settimeout(0.5)
    return client


def stop_client(client):
    if client:
        client.shutdown(socket.SHUT_RDWR)
        client.close()


class PackageTestCase(DeferrableTestCase):
    @classmethod
    def setUpClass(self):
        self.executor = futures.ThreadPoolExecutor()
        sublime.run_command("new_window")
        self.window = sublime.active_window()

    @classmethod
    def tearDownClass(self):
        if self.window:
            self.window.run_command("close_window")

        self.executor.shutdown(wait=False)

    def setUp(self, syntax="Clojure (Tutkain).sublime-syntax"):
        self.view = self.window.new_file()
        self.view.set_name("tutkain.clj")
        self.view.set_scratch(True)

        if window := self.view.window():
            window.focus_view(self.view)

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

    def eval_context(self, file="NO_SOURCE_FILE", ns=edn.Symbol("user"), line=1, column=1):
        actual = edn.read(self.server.backchannel.recv())

        id = actual.get(edn.Keyword("id"))

        message = edn.kwmap({
             "id": id,
             "op": edn.Keyword("set-eval-context"),
             "file": file,
             "ns": ns,
             "line": line,
             "column": column,
        })

        self.assertEquals(message, actual)

        response = edn.kwmap({
            "id": id,
            "result": edn.Keyword("ok")
        })

        self.server.backchannel.send(response)

