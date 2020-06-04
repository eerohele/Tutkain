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
