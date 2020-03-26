import sublime
import sys
import os
import time

from unittest import TestCase

sys.path.append(os.path.join(os.path.dirname(__file__), 'dependencies'))

import edn_format
from edn_format import Keyword

tutkain = sys.modules["Tutkain.tutkain"]
brackets = sys.modules["Tutkain.brackets"]


class TestReplClient(TestCase):
    def test_repl_client(self):
        # You have to start a socket REPL on localhost:12345 to run this test.
        with tutkain.ReplClient('localhost', 12345) as repl_client:
            repl_client.input.put('(+ 1 2 3)')
            self.assertEquals(repl_client.output.get().get(Keyword('val')), '6')

    def test_find_rbracket_balanced(self):
        pos = brackets.find_rbracket(
            lambda p: p >= 5 and p < 11,
            brackets.LPAREN, brackets.RPAREN,
            '(foo "bar)")',
            0
        )

        self.assertEquals(pos, 11)

        pos = brackets.find_rbracket(
            lambda *args: False,
            brackets.LPAREN, brackets.RPAREN,
            '((()))',
            1
        )

        self.assertEquals(pos, 4)

    def test_find_rbracket_unbalanced(self):
        pos = brackets.find_rbracket(
            lambda p: p >= 5 and p < 11,
            brackets.LPAREN, brackets.RPAREN,
            '(foo "bar)"',
            0
        )

        self.assertEquals(pos, None)

    def test_find_lbracket_balanced(self):
        pos = brackets.find_lbracket(
            lambda p: p >= 5 and p < 11,
            brackets.LPAREN, brackets.RPAREN,
            '(foo "(bar")',
            11
        )

        self.assertEquals(pos, 0)

        pos = brackets.find_lbracket(
            lambda *args: False,
            brackets.LPAREN, brackets.RPAREN,
            '((()))"',
            4
        )

        self.assertEquals(pos, 1)

    def test_find_lbracket_unbalanced(self):
        pos = brackets.find_lbracket(
            lambda p: p >= 5 and p < 12,
            '(', ')',
            'foo "(bar")',
            11
        )

        self.assertEquals(pos, None)

    def test_find_nearest_lbracket(self):
        pos = brackets.find_nearest_lbracket(
            lambda p: p >= 6 and p < 10,
            brackets.LPAREN,
            '(foo "(bar")',
            7
        )

        self.assertEquals(pos, 0)

    def test_find_nearest_rbracket(self):
        pos = brackets.find_nearest_rbracket(
            lambda p: p >= 6 and p < 10,
            brackets.RPAREN,
            '(foo ")bar")',
            7
        )

        self.assertEquals(pos, 11)

    def test_find_any_nearest_lbracket(self):
        never = lambda *args: False

        match = brackets.find_any_nearest_lbracket(never, '@(bar)', 2)
        self.assertEquals(match, (brackets.LPAREN, 1))

        match = brackets.find_any_nearest_lbracket(never, '[bar]', 3)
        self.assertEquals(match, (brackets.LBRACKET, 0))

        match = brackets.find_any_nearest_lbracket(never, '{bar}', 3)
        self.assertEquals(match, (brackets.LBRACE, 0))

        ignore = lambda p: p == 2 or p == 3 or p == 5 or p == 6
        match = brackets.find_any_nearest_lbracket(ignore, ' {"(" ")"} ', 4)
        self.assertEquals(match, (brackets.LBRACE, 1))

    def test_current_form_range(self):
        never = lambda *args: False

        start, end = brackets.current_form_range(never, '(foo)', 1)
        self.assertEquals((start, end), (0, 4))

        # TODO: How do I want this to work, actually? Now prefers parens over
        # other brackets.
        start, end = brackets.current_form_range(never, '({:a :b} :a)', 2)
        self.assertEquals((start, end), (0, 11))

        start, end = brackets.current_form_range(never, '(str ["["])', 6)
        self.assertEquals((start, end), (0, 10))

        start, end = brackets.current_form_range(never, ' ["("]', 2)
        self.assertEquals((start, end), (1, 5))

        start, end = brackets.current_form_range(never, ' ["("]', 1)
        self.assertEquals((start, end), (1, 5))

        match = brackets.current_form_range(never, ' ["("]', 0)
        self.assertEquals(match, None)
