import sublime
from unittest import TestCase


class ViewTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.assign_syntax('Packages/Clojure/Clojure.sublime-syntax')

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('close_file')

    def setUp(self):
        self.view.run_command('select_all')
        self.view.run_command('right_delete')

    def view_content(self):
        return self.view.substr(sublime.Region(0, self.view.size()))

    def append_to_view(self, chars):
        self.view.run_command('append', {'characters': chars})

    def add_cursors(self, *points):
        self.view.sel().clear()

        for point in points:
            self.view.sel().add(sublime.Region(point))

    def selections(self):
        return [(region.begin(), region.end()) for region in self.view.sel()]

    def selection(self, i):
        return self.view.substr(self.view.sel()[i])
