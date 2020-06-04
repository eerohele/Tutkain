from inspect import cleandoc
import sublime

from tutkain import tutkain
from unittest import TestCase


from .util import ViewTestCase


class TestOpenRoundCommand(ViewTestCase):
    def test_open_round(self):
        self.append_to_view('(a b c d)')
        self.set_selections((5, 5))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals(self.view_content(), '(a b () c d)')
        self.assertEquals(self.selections(), [(6, 6)])

    def test_open_round_next_to_whitespace(self):
        self.append_to_view('(a b c d)')
        self.set_selections((9, 9))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals(self.view_content(), '(a b c d)()')
        self.assertEquals(self.selections(), [(10, 10)])

    def test_open_round_inside_string(self):
        self.append_to_view('(foo "bar baz" quux)')
        self.set_selections((10, 10))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals(self.view_content(), '(foo "bar (baz" quux)')
        self.assertEquals(self.selections(), [(11, 11)])

    def test_open_round_multiple_cursors(self):
        self.append_to_view('(a b c d) (e f g h)')
        self.set_selections((5, 5), (15, 15))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals(self.view_content(), '(a b () c d) (e f () g h)')
        self.assertEquals(self.selections(), [(6, 6), (19, 19)])

    def test_open_round_selection(self):
        self.append_to_view('(a b c)')
        self.set_selections((3, 4))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals(self.view_content(), '(a (b) c)')
        self.assertEquals(self.selections(), [(4, 4)])

    def test_open_round_before_close_paren(self):
        self.append_to_view('(a )')
        self.set_selections((3, 3))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals(self.view_content(), '(a ())')
        self.assertEquals(self.selections(), [(4, 4)])

    def test_open_round_before_close_paren(self):
        self.append_to_view('(a [b ])')
        self.set_selections((6, 6))
        self.view.run_command('tutkain_paredit_open_round')
        self.assertEquals(self.view_content(), '(a [b ()])')
        self.assertEquals(self.selections(), [(7, 7)])

    def test_close_round(self):
        self.append_to_view('(a )')
        self.set_selections((2, 2))
        self.view.run_command('tutkain_paredit_close_round')
        self.assertEquals(self.view_content(), '(a)')
        self.assertEquals(self.selections(), [(3, 3)])

    def test_close_round_multiple_cursors(self):
        self.append_to_view('(a ) (b )')
        self.set_selections((2, 2), (7, 7))
        self.view.run_command('tutkain_paredit_close_round')
        self.assertEquals(self.view_content(), '(a) (b)')
        self.assertEquals(self.selections(), [(3, 3), (7, 7)])

    def test_double_quote_simple(self):
        self.set_selections((0, 0))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals(self.view_content(), '""')
        self.assertEquals(self.selections(), [(1, 1)])

    def test_double_quote_inside_string(self):
        self.append_to_view('" "')
        self.set_selections((1, 1))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals(self.view_content(), '"\\" "')
        self.assertEquals(self.selections(), [(3, 3)])

    def test_double_quote_next_to_left_double_quote(self):
        self.append_to_view('""')
        self.set_selections((0, 0))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals(self.view_content(), '""')
        self.assertEquals(self.selections(), [(1, 1)])

    def test_double_quote_next_to_right_double_quote(self):
        self.append_to_view('""')
        self.set_selections((1, 1))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals(self.view_content(), '""')
        self.assertEquals(self.selections(), [(2, 2)])

    def test_double_quote_inside_comment(self):
        self.append_to_view('; ')
        self.set_selections((2, 2))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals(self.view_content(), '; "')
        self.assertEquals(self.selections(), [(3, 3)])

    def test_double_quote_multiple_cursors(self):
        self.append_to_view(' ')
        self.set_selections((0, 0), (1, 1))
        self.view.run_command('tutkain_paredit_double_quote')
        self.assertEquals(self.view_content(), '"" ""')
        self.assertEquals(self.selections(), [(1, 1), (4, 4)])
        self.view.run_command(('tutkain_paredit_double_quote'))
        self.assertEquals(self.selections(), [(2, 2), (5, 5)])
