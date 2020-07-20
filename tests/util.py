import sublime
from unittest import TestCase


class ViewTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.assign_syntax('Clojure (Tutkain).sublime-syntax')

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('close_file')

    def setUp(self):
        self.clear_view()

    def view_content(self):
        return self.view.substr(sublime.Region(0, self.view.size()))

    def clear_view(self):
        self.view.run_command('select_all')
        self.view.run_command('right_delete')

    def set_view_content(self, chars):
        self.clear_view()
        self.view.run_command('append', {'characters': chars})

    def set_selections(self, *pairs):
        self.view.sel().clear()

        for begin, end in pairs:
            self.view.sel().add(sublime.Region(begin, end))

    def selections(self):
        return [(region.begin(), region.end()) for region in self.view.sel()]

    def selection(self, i):
        return self.view.substr(self.view.sel()[i])
