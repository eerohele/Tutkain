import sublime

from Tutkain.api import edn
from Tutkain.src.repl import views
from Tutkain.src.repl import tap
from unittest import TestCase


def view_content(view):
    return view.substr(sublime.Region(0, view.size()))


def reset_view(view):
    view.set_read_only(False)
    view.run_command("select_all")
    view.run_command("right_delete")


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
        views.configure(self.repl_view, edn.Keyword("clj"), "1", "localhost", 1234)

        # Clear both views by default:

        self.repl_view.run_command("append", {"characters": "foo"})
        self.tap_panel.run_command("append", {"characters": "bar"})

        self.window.run_command("tutkain_clear_output_view")

        self.assertEquals("", view_content(self.repl_view))
        self.assertEquals("", view_content(self.tap_panel))


        # Explicit pass "tap" and "repl":

        reset_view(self.repl_view)
        reset_view(self.tap_panel)

        self.repl_view.run_command("append", {"characters": "foo"})
        self.tap_panel.run_command("append", {"characters": "bar"})

        self.window.run_command("tutkain_clear_output_view", {"views": ["tap", "repl"]})

        self.assertEquals("", view_content(self.repl_view))
        self.assertEquals("", view_content(self.tap_panel))


        # Clear "tap" only:

        reset_view(self.repl_view)
        reset_view(self.tap_panel)

        self.repl_view.run_command("append", {"characters": "foo"})
        self.tap_panel.run_command("append", {"characters": "bar"})

        self.window.run_command("tutkain_clear_output_view", {"views": ["tap"]})

        self.assertEquals("foo", view_content(self.repl_view))
        self.assertEquals("", view_content(self.tap_panel))


        # Clear "repl" only:

        reset_view(self.repl_view)
        reset_view(self.tap_panel)

        self.repl_view.run_command("append", {"characters": "foo"})
        self.tap_panel.run_command("append", {"characters": "bar"})

        self.window.run_command("tutkain_clear_output_view", {"views": ["repl"]})

        self.assertEquals("", view_content(self.repl_view))
        self.assertEquals("bar", view_content(self.tap_panel))


        # Clear none:

        reset_view(self.repl_view)
        reset_view(self.tap_panel)

        self.repl_view.run_command("append", {"characters": "foo"})
        self.tap_panel.run_command("append", {"characters": "bar"})

        self.window.run_command("tutkain_clear_output_view", {"views": []})

        self.assertEquals("foo", view_content(self.repl_view))
        self.assertEquals("bar", view_content(self.tap_panel))
