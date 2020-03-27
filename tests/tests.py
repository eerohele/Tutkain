import sublime
import sys
import os
import time

from unittest import TestCase

sys.path.append(os.path.join(os.path.dirname(__file__), 'dependencies'))

import edn_format
from edn_format import Keyword

import Tutkain.tutkain as tutkain
import Tutkain.brackets as brackets


class TestReplClient(TestCase):
    def setUp(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.set_syntax_file('Packages/Clojure/Clojure.tmLanguage')

    def tearDown(self):
        if self.view:
            self.view.window().run_command('close_file')

    def set_view_content(self, chars):
        self.view.run_command('append', {'characters': chars})

    def test_repl_client(self):
        # You have to start a socket REPL on localhost:12345 to run this test.
        with tutkain.ReplClient('localhost', 12345) as repl_client:
            repl_client.input.put('(+ 1 2 3)')
            self.assertEquals(repl_client.output.get().get(Keyword('val')), '6')

    def form(self, pos):
        return self.view.substr(brackets.current_form_region(self.view, pos))

    def test_current_form_region_simple(self):
        form = '(+ 1 2)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_brackets(self):
        form = '[1 [2 3] 4]'
        self.set_view_content(form)
        self.assertEquals(self.form(0), form)
        self.assertEquals(self.form(len(form)), form)
        self.assertEquals(self.form(3), '[2 3]')

    def test_current_form_region_mixed(self):
        form = '(a {:b :c} [:d] )'
        self.set_view_content(form)
        self.assertEquals(self.form(5), '{:b :c}')
        self.assertEquals(self.form(11), '[:d]')
        self.assertEquals(self.form(16), form)

    def test_current_form_region_set(self):
        form = '#{1 2 3}'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_discard(self):
        form = '(inc #_(dec 2) 4)'
        self.set_view_content(form)
        self.assertEquals(self.form(7), '(dec 2)')
        self.assertEquals(self.form(12), '(dec 2)')
        self.assertEquals(self.form(12), '(dec 2)')
        self.assertEquals(self.form(14), '(dec 2)')
        self.assertEquals(self.form(16), form)
