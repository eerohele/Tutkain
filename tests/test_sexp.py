import sublime
from unittest import skip, TestCase

from tutkain import sexp
from .util import ViewTestCase


class TestSexp(ViewTestCase):
    def current(self, point, ignore={}):
        view = self.view
        region = sexp.outermost(view, point, absorb=True, ignore=ignore)

        if region:
            return view.substr(region)

    def innermost(self, pos):
        region = sexp.innermost(self.view, pos)

        if region:
            return self.view.substr(region)

    def outermost(self, pos):
        region = sexp.outermost(self.view, pos)

        if region:
            return self.view.substr(region)

    def test_inside_string(self):
        content = ' "x" '
        self.set_view_content(content)
        self.assertEquals(
            list(
                map(
                    lambda point: sexp.inside_string(self.view, point),
                    range(0, len(content))
                )
            ),
            [False, False, True, True, False]
        )
        # TODO: Test backslash escape scenarios

    def test_innermost_simple(self):
        form = '(a (b) c)'
        self.set_view_content(form)
        self.assertEquals(self.innermost(0), form)
        self.assertEquals(self.innermost(1), form)
        self.assertEquals(self.innermost(2), form)
        self.assertEquals(self.innermost(3), '(b)')
        self.assertEquals(self.innermost(4), '(b)')
        self.assertEquals(self.innermost(5), '(b)')
        self.assertEquals(self.innermost(6), '(b)')
        self.assertEquals(self.innermost(7), form)
        self.assertEquals(self.innermost(8), form)
        self.assertEquals(self.innermost(9), form)

    def test_current_simple(self):
        form = '(+ 1 2)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_current_sexp(self):
        form = '[1 [2 3] 4]'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_current_mixed(self):
        form = '(a {:b :c} [:d] )'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_current_set(self):
        form = '#{1 2 3}'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_current_deref_sexp(self):
        form = '@(atom 1)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_current_lambda(self):
        form = '#(+ 1 2 3)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_current_discard(self):
        form = '(inc #_(dec 2) 4)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_current_string_next_to_lbracket(self):
        form = '(merge {"A" :B})'
        self.set_view_content(form)
        self.assertEquals(self.current(len(form)), form)

    def test_current_ignore_string_1(self):
        form = '(a "()" b)'
        self.set_view_content(form)
        self.assertEquals(self.current(len(form)), form)

    def test_current_ignore_string_2(self):
        form = '(a "\"()\"" b)'
        self.set_view_content(form)
        self.assertEquals(self.current(len(form)), form)

    def test_current_none_when_outside_sexp(self):
        form = '"#{"'
        self.set_view_content(form)
        self.assertEquals(self.current(1), None)

    def test_current_adjacent_parens(self):
        form = '((resolving-require \'clojure.test/run-tests))'
        self.set_view_content(form)
        self.assertEquals(self.current(0), form)
        self.assertEquals(self.current(1), form)
        self.assertEquals(self.current(44), form)
        self.assertEquals(self.current(45), form)

    def test_current_ignore_comment_list(self):
        form = '(comment (+ 1 1))'
        self.set_view_content(form)
        self.assertEquals(self.current(0, ignore={'comment'}), form)
        self.assertEquals(self.current(1, ignore={'comment'}), form)
        for n in range(9, 16):
            self.assertEquals(self.current(n, ignore={'comment'}), '(+ 1 1)')

    def test_current_ignore_comment_set(self):
        form = '(comment #{1 2 3})'
        self.set_view_content(form)
        self.assertEquals(self.current(0, ignore={'comment'}), form)
        self.assertEquals(self.current(1, ignore={'comment'}), form)
        for n in range(9, 17):
            self.assertEquals(self.current(n, ignore={'comment'}), '#{1 2 3}')

    def test_current_quote(self):
        form = '\'(1 2 3)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.current(n), form)

    def test_outermost(self):
        form = '(a (b))'
        self.set_view_content(form)

        for n in range(len(form)):
            self.assertEquals(self.outermost(0), form)

    def test_cycle_collection_type(self):
        content = '(a b)'
        self.set_view_content(content)

        for n in range(len(content)):
            self.set_selections((n, n))
            self.view.run_command('tutkain_cycle_collection_type')
            self.assertEquals('[a b]', self.view_content())
            self.view.run_command('tutkain_cycle_collection_type')
            self.assertEquals('{a b}', self.view_content())
            self.view.run_command('tutkain_cycle_collection_type')
            self.assertEquals('#{a b}', self.view_content())
            self.view.run_command('tutkain_cycle_collection_type')
            self.assertEquals('(a b)', self.view_content())

    def test_cycle_collection_type_multiple_cursors(self):
        self.set_view_content('(a b) [c d]')
        self.set_selections((0, 0), (6, 6))
        self.view.run_command('tutkain_cycle_collection_type')
        self.assertEquals('[a b] {c d}', self.view_content())
        self.view.run_command('tutkain_cycle_collection_type')
        self.assertEquals('{a b} #{c d}', self.view_content())
        self.view.run_command('tutkain_cycle_collection_type')
        self.assertEquals('#{a b} (c d)', self.view_content())
        self.view.run_command('tutkain_cycle_collection_type')
        self.assertEquals('(a b) [c d]', self.view_content())

    @skip('not implemented')
    def test_cycle_collection_type_cursor_position(self):
        self.set_view_content('{a b} {c d}')
        self.set_selections((0, 0), (6, 6))
        self.view.run_command('tutkain_cycle_collection_type')
        self.assertEquals('#{a b} #{c d}', self.view_content())
        self.assertEquals([(0, 0), (7, 7)], self.selections())
