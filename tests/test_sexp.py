from sublime import Region
from unittest import skip

from tutkain import sexp
from .util import ViewTestCase


class TestSexp(ViewTestCase):
    def test_find_open(self):
        self.set_view_content('(a)')
        self.assertEquals((None, None), sexp.find_open(self.view, 0))
        self.assertEquals(('(', Region(0, 1)), sexp.find_open(self.view, 1))
        self.assertEquals((None, None), sexp.find_open(self.view, 3))
        self.set_view_content('(a [b] c)')
        self.assertEquals(('[', Region(3, 4)), sexp.find_open(self.view, 4))
        self.assertEquals(('(', Region(0, 1)), sexp.find_open(self.view, 6))

    def test_find_close(self):
        self.set_view_content('(a)')
        self.assertEquals(None, sexp.find_close(self.view, 0))
        self.assertEquals(Region(2, 3), sexp.find_close(self.view, 1, close=')'))
        self.set_view_content('(a [b] c)')
        self.assertEquals(Region(5, 6), sexp.find_close(self.view, 4, close=']'))
        self.assertEquals(Region(8, 9), sexp.find_close(self.view, 6, close=')'))

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
        self.set_view_content('(a (b) c)')
        self.assertEquals(sexp.innermost(self.view, 0).extent(), Region(0, 9))
        self.assertEquals(sexp.innermost(self.view, 1).extent(), Region(0, 9))
        self.assertEquals(sexp.innermost(self.view, 2).extent(), Region(0, 9))
        self.assertEquals(sexp.innermost(self.view, 3).extent(), Region(3, 6))
        self.assertEquals(sexp.innermost(self.view, 4).extent(), Region(3, 6))
        self.assertEquals(sexp.innermost(self.view, 5).extent(), Region(3, 6))
        self.assertEquals(sexp.innermost(self.view, 6).extent(), Region(3, 6))
        self.assertEquals(sexp.innermost(self.view, 7).extent(), Region(0, 9))
        self.assertEquals(sexp.innermost(self.view, 8).extent(), Region(0, 9))
        self.assertEquals(sexp.innermost(self.view, 9).extent(), Region(0, 9))

    def test_innermost_next_to_string(self):
        content = '"a"'
        self.set_view_content(content)
        self.assertEquals(sexp.innermost(self.view, 0).extent(), Region(0, 3))

    def test_innermost_empty_string_in_brackets(self):
        form = '("")'
        self.set_view_content(form)
        self.assertEquals(sexp.innermost(self.view, 2).extent(), Region(1, 3))

    def test_outermost_simple(self):
        form = '(+ 1 2)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost_sexp(self):
        form = '[1 [2 3] 4]'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost_mixed(self):
        form = '(a {:b :c} [:d] )'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost_set(self):
        form = '#{1 2 3}'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost_deref_sexp(self):
        form = '@(atom 1)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost_lambda(self):
        form = '#(+ 1 2 3)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost_discard(self):
        form = '(inc #_(dec 2) 4)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost_string_next_to_lbracket(self):
        form = '(merge {"A" :B})'
        self.set_view_content(form)
        self.assertEquals(sexp.outermost(self.view, len(form)).extent(), Region(0, len(form)))

    def test_outermost_ignore_string_1(self):
        form = '(a "()" b)'
        self.set_view_content(form)
        self.assertEquals(sexp.outermost(self.view, len(form)).extent(), Region(0, len(form)))

    def test_outermost_ignore_string_2(self):
        form = '(a "\"()\"" b)'
        self.set_view_content(form)
        self.assertEquals(sexp.outermost(self.view, len(form)).extent(), Region(0, len(form)))

    @skip('not implemented -- unnecessary?')
    def test_outermost_inside_string(self):
        form = '"a"'
        self.set_view_content(form)
        self.assertEquals(sexp.outermost(self.view, 1).extent(), Region(0, len(form)))
        self.assertEquals(sexp.outermost(self.view, 2).extent(), Region(0, len(form)))

    def test_outermost_adjacent_parens(self):
        form = '((resolving-require \'clojure.test/run-tests))'
        self.set_view_content(form)
        self.assertEquals(sexp.outermost(self.view, 0).extent(), Region(0, len(form)))
        self.assertEquals(sexp.outermost(self.view, 1).extent(), Region(0, len(form)))
        self.assertEquals(sexp.outermost(self.view, 44).extent(), Region(0, len(form)))
        self.assertEquals(sexp.outermost(self.view, 45).extent(), Region(0, len(form)))

    def test_outermost_ignore_comment_list(self):
        form = '(comment (+ 1 1))'
        self.set_view_content(form)
        self.assertEquals(sexp.outermost(self.view, 0, ignore={'comment'}).extent(), Region(0, len(form)))
        self.assertEquals(sexp.outermost(self.view, 1, ignore={'comment'}).extent(), Region(0, len(form)))
        for n in range(9, 16):
            self.assertEquals(sexp.outermost(self.view, n, ignore={'comment'}).extent(), Region(9, 16))

    def test_outermost_ignore_comment_set(self):
        form = '(comment #{1 2 3})'
        self.set_view_content(form)
        self.assertEquals(sexp.outermost(self.view, 0, ignore={'comment'}).extent(), Region(0, len(form)))
        self.assertEquals(sexp.outermost(self.view, 1, ignore={'comment'}).extent(), Region(0, len(form)))
        for n in range(9, 17):
            self.assertEquals(sexp.outermost(self.view, n, ignore={'comment'}).extent(), Region(9, 17))

    def test_outermost_quote(self):
        form = '\'(1 2 3)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, len(form)))

    def test_outermost(self):
        form = '(a (b))'
        self.set_view_content(form)

        for n in range(len(form)):
            self.assertEquals(sexp.outermost(self.view, n).extent(), Region(0, 7))

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

    def test_find_next_element(self):
        self.set_view_content('a')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 1))
        self.set_view_content(':foo')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 4))
        self.set_view_content(':foo/bar')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 8))
        self.set_view_content('(identity 1/2)')
        self.assertEquals(sexp.find_next_element(self.view, 10), Region(10, 13))
        self.set_view_content('(identity 0.2)')
        self.assertEquals(sexp.find_next_element(self.view, 10), Region(10, 13))
        self.set_view_content('(a (b) c)')
        self.assertEquals(sexp.find_next_element(self.view, 2), Region(3, 6))
        self.set_view_content('(a (b) c)')
        self.assertEquals(sexp.find_next_element(self.view, 3), Region(3, 6))
        self.set_view_content('abc?')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 4))
        self.set_view_content('<abc>')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 5))
        self.set_view_content('=abc=')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 5))
        self.set_view_content('+abc+')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 5))
        self.set_view_content('!abc!')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 5))
        self.set_view_content('*abc*')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 5))
        self.set_view_content('äöå')
        self.assertEquals(sexp.find_next_element(self.view, 0), Region(0, 3))
        self.set_view_content('(ns ^:foo bar.baz)')
        self.assertEquals(sexp.find_next_element(self.view, 3), Region(4, 9))
        self.set_view_content('''(foo 'bar)''')
        self.assertEquals(sexp.find_next_element(self.view, 4), Region(5, 9))
        self.set_view_content('''(foo 'bar baz)''')
        self.assertEquals(sexp.find_next_element(self.view, 4), Region(5, 9))
        self.set_view_content('''(foo #'bar baz)''')
        self.assertEquals(sexp.find_next_element(self.view, 4), Region(5, 10))

    def test_find_previous_element(self):
        self.set_view_content('a')
        self.assertEquals(sexp.find_previous_element(self.view, 1), Region(0, 1))
        self.set_view_content(':foo')
        self.assertEquals(sexp.find_previous_element(self.view, 4), Region(0, 4))
        self.set_view_content(':foo/bar')
        self.assertEquals(sexp.find_previous_element(self.view, 8), Region(0, 8))
        self.set_view_content('(identity 1/2)')
        self.assertEquals(sexp.find_previous_element(self.view, 13), Region(10, 13))
        self.set_view_content('(identity 0.2)')
        self.assertEquals(sexp.find_previous_element(self.view, 13), Region(10, 13))
        self.set_view_content('(a (b) c)')
        self.assertEquals(sexp.find_previous_element(self.view, 6), Region(3, 6))
        self.set_view_content('(a (b) c)')
        self.assertEquals(sexp.find_previous_element(self.view, 7), Region(3, 6))
        self.set_view_content('abc?')
        self.assertEquals(sexp.find_previous_element(self.view, 4), Region(0, 4))
        self.set_view_content('<abc>')
        self.assertEquals(sexp.find_previous_element(self.view, 5), Region(0, 5))
        self.set_view_content('=abc=')
        self.assertEquals(sexp.find_previous_element(self.view, 5), Region(0, 5))
        self.set_view_content('+abc+')
        self.assertEquals(sexp.find_previous_element(self.view, 5), Region(0, 5))
        self.set_view_content('!abc!')
        self.assertEquals(sexp.find_previous_element(self.view, 5), Region(0, 5))
        self.set_view_content('*abc*')
        self.assertEquals(sexp.find_previous_element(self.view, 5), Region(0, 5))
        self.set_view_content('äöå')
        self.assertEquals(sexp.find_previous_element(self.view, 3), Region(0, 3))
        self.set_view_content('(ns ^:foo bar.baz)')
        self.assertEquals(sexp.find_previous_element(self.view, 10), Region(4, 9))
        self.set_view_content('''(foo 'bar)''')
        self.assertEquals(sexp.find_previous_element(self.view, 9), Region(5, 9))
        self.set_view_content('''(foo 'bar baz)''')
        self.assertEquals(sexp.find_previous_element(self.view, 10), Region(5, 9))
        self.set_view_content('''(foo #'bar baz)''')
        self.assertEquals(sexp.find_previous_element(self.view, 11), Region(5, 10))
        self.set_view_content('(foo "bar")')
        self.assertEquals(sexp.find_previous_element(self.view, 10), Region(5, 10))
