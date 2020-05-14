import sublime
from unittest import TestCase


class TestBrackets(TestCase):
    @classmethod
    def setUpClass(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        # requires https://github.com/oconnor0/Clojures
        self.view.set_syntax_file('Packages/Clojures/Clojure.tmLanguage')

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('close_file')

    def setUp(self):
        self.view.run_command('select_all')
        self.view.run_command('right_delete')

    def append_to_view(self, chars):
        self.view.run_command('append', {'characters': chars})

    def move_cursor(self, pos):
        self.view.sel().clear()
        self.view.sel().add(sublime.Region(pos))

    def selection(self, i):
        return self.view.substr(self.view.sel()[i])

    def expand(self):
        self.view.run_command('tutkain_expand_selection')

    def test_before_lparen(self):
        self.append_to_view('(foo)')
        self.move_cursor(0)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_after_lparen(self):
        self.append_to_view('(foo)')
        self.move_cursor(1)
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_after_rparen(self):
        self.append_to_view('(foo)')
        self.move_cursor(6)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_before_lbracket(self):
        self.append_to_view('[foo]')
        self.move_cursor(0)
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_after_lbracket(self):
        self.append_to_view('[foo]')
        self.move_cursor(1)
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_after_rbracket(self):
        self.append_to_view('[foo]')
        self.move_cursor(6)
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_before_lcurly(self):
        self.append_to_view('{:a 1}')
        self.move_cursor(0)
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    def test_after_lcurly(self):
        self.append_to_view('{:a 1}')
        self.move_cursor(1)
        self.expand()
        self.assertEquals(self.selection(0), ':a')

    def test_after_rcurly(self):
        self.append_to_view('{:a 1}')
        self.move_cursor(7)
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    def test_before_set(self):
        self.append_to_view('#{1}')
        self.move_cursor(0)
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_set_hash_and_bracket(self):
        self.append_to_view('#{1}')
        self.move_cursor(1)
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_on_symbol(self):
        self.append_to_view('(inc 1)')
        self.move_cursor(2)
        self.expand()
        self.assertEquals(self.selection(0), 'inc')

    def test_before_at(self):
        self.append_to_view('@(foo)')
        self.move_cursor(0)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at(self):
        self.append_to_view('@(foo)')
        self.move_cursor(1)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at_rparen(self):
        self.append_to_view('@(foo)')
        self.move_cursor(6)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')
