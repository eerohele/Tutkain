import re
import sublime
import time

from unittest import TestCase


def wait_until(pred, delay=0.25, retries=50):
    retries_left = retries

    while retries_left >= 0:
        if pred():
            return True
        else:
            time.sleep(delay)
            retries_left -= 1

    return False


def wait_until_equals(a, b, delay=0.25, retries=50):
    return wait_until(lambda: a == b(), delay, retries)


def wait_until_matches(a, b, delay=0.25, retries=50):
    return wait_until(lambda: re.search(a, b()), delay, retries)


def wait_until_contains(a, b, delay=0.25, retries=50):
    return wait_until(lambda: a in b(), delay, retries)


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

    def assertEqualsEventually(self, a, b):
        if not wait_until_equals(a, b):
            raise AssertionError("'{}' != '{}'".format(a, b()))

    def assertMatchesEventually(self, a, b):
        if not wait_until_matches(a, b):
            raise AssertionError("'{}' does not match '{}'".format(a, b()))

    def assertContainsEventually(self, a, b):
        if not wait_until_contains(a, b):
            raise AssertionError("'{}' does not contain '{}'".format(a, b()))
