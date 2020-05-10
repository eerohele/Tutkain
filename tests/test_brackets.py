import sublime
from unittest import TestCase, skip

from tutkain import brackets


class TestBrackets(TestCase):
    @classmethod
    def setUpClass(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.set_syntax_file('Packages/Clojure/Clojure.tmLanguage')

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('close_file')

    def setUp(self):
        self.view.run_command('select_all')
        self.view.run_command('right_delete')

    def append_to_view(self, chars):
        self.view.run_command('append', {'characters': chars})

    def form(self, pos):
        region = brackets.current_form_region(self.view, pos)

        if region:
            return self.view.substr(region)

    def test_current_form_region_simple(self):
        form = '(+ 1 2)'
        self.append_to_view(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_brackets(self):
        form = '[1 [2 3] 4]'
        self.append_to_view(form)
        self.assertEquals(self.form(0), form)
        self.assertEquals(self.form(len(form)), form)
        self.assertEquals(self.form(3), '[2 3]')

    def test_current_form_region_mixed(self):
        form = '(a {:b :c} [:d] )'
        self.append_to_view(form)
        self.assertEquals(self.form(5), '{:b :c}')
        self.assertEquals(self.form(11), '[:d]')
        self.assertEquals(self.form(16), form)

    def test_current_form_region_set(self):
        form = '#{1 2 3}'
        self.append_to_view(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_deref_sexp(self):
        form = '@(atom 1)'
        self.append_to_view(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_lambda(self):
        form = '#(+ 1 2 3)'
        self.append_to_view(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_discard(self):
        form = '(inc #_(dec 2) 4)'
        self.append_to_view(form)
        self.assertEquals(self.form(7), '(dec 2)')
        self.assertEquals(self.form(12), '(dec 2)')
        self.assertEquals(self.form(12), '(dec 2)')
        self.assertEquals(self.form(14), '(dec 2)')
        self.assertEquals(self.form(16), form)

    def test_string_next_to_lbracket(self):
        form = '(merge {"A" :B})'
        self.append_to_view(form)
        self.assertEquals(self.form(len(form)), form)

    def test_ignore_string_1(self):
        form = '(a "()" b)'
        self.append_to_view(form)
        self.assertEquals(self.form(len(form)), form)

    def test_ignore_string_2(self):
        form = '(a "\"()\"" b)'
        self.append_to_view(form)
        self.assertEquals(self.form(len(form)), form)

    @skip('not implemented')
    def test_none_when_outside_sexp(self):
        form = '"#{"'
        self.append_to_view(form)
        self.assertEquals(self.form(1), None)
