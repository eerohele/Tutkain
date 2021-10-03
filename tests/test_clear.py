import sublime

from Tutkain.api import edn
from Tutkain.src.repl import views
from Tutkain.src.repl import tap
from unittest import TestCase


def view_content(view):
    return view.substr(sublime.Region(0, view.size()))


class TestClear(TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.repl_view = self.window.new_file()
        self.tap_panel = tap.create_panel(self.window)

    def tearDown(self):
        if self.tap_panel:
            self.tap_panel.close()

        if self.repl_view:
            self.repl_view.close()

    def test_clear(self):
        views.configure(self.repl_view, edn.Keyword("clj"), "localhost", 1234)
        self.repl_view.run_command("append", {"characters": "foo"})
        self.tap_panel.run_command("append", {"characters": "bar"})
        self.window.run_command("tutkain_clear_output_view")
        self.assertEquals("", view_content(self.repl_view))
        self.assertEquals("", view_content(self.tap_panel))
