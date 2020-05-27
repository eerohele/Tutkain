import sublime
import time

from unittest import skip, TestCase
from .util import ViewTestCase


class TestCommands(ViewTestCase):
    delay = 0.15

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.view.window().run_command(
            'tutkain_connect',
            {'host': 'localhost', 'port': 1234}
        )

        self.output_panel = self.view.window().find_output_panel('tutkain')

    def output_panel_content(self):
        return self.output_panel.substr(sublime.Region(0, self.output_panel.size()))

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('tutkain_disconnect')
            self.view.window().destroy_output_panel('tutkain')
            self.view.window().run_command('close_file')

    def setUp(self):
        super().setUp()
        self.view.window().run_command('tutkain_clear_output_panel')

    def test_evaluate_form(self):
        content = '(+ 1 2)'
        self.append_to_view(content)
        self.add_cursors(0)
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            self.output_panel_content(),
            ''';; => (+ 1 2)\n3\n'''
        )

    def test_evaluate_view(self):
        content = '''(ns app.core) (defn square [x] (* x x))'''
        self.append_to_view(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertEquals(
            self.output_panel_content(),
            ''';; Loading view...\n'''
        )

        self.append_to_view(' (square 2)')
        self.add_cursors(40)
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            self.output_panel_content(),
            ''';; Loading view...
;; => (square 2)
4
''')

    def test_evaluate_view_with_error(self):
        content = '''(ns app.core) (inc "a")'''
        self.append_to_view(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertRegex(
            self.output_panel_content(),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

    def test_run_test_in_current_namespace(self):
        content = '''(ns app.core-test
        (:require [clojure.test :refer [deftest is]]))

        (deftest ok (is (=  2 (+ 1 1))))
        (deftest nok (is (=  3 (+ 1 1))))
        '''
        self.append_to_view(content)
        self.view.run_command('tutkain_run_tests_in_current_namespace')
        time.sleep(self.delay)

        self.assertEquals(
            self.output_panel_content().splitlines()[-1],
            '''{:test 2, :pass 1, :fail 1, :error 0, :type :summary}'''
        )

    def test_run_test_in_current_namespace_with_error(self):
        content = '''(ns error.core-test
        (:require [clojure.test :refer [deftest is]]))

        (deftest test-with-error (is (= "JavaScript" (+ 1 "a"))))
        '''
        self.append_to_view(content)
        self.view.run_command('tutkain_run_tests_in_current_namespace')
        time.sleep(self.delay)

        self.assertRegex(
            self.output_panel_content(),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

    # TODO: Figure out how to test EvaluateInputCommand

    def test_interrupt_evaluation(self):
        content = '''(do (Thread/sleep 1000) (println "Boom!"))'''
        self.append_to_view(content)
        self.add_cursors(0)
        self.view.run_command('tutkain_evaluate_form')
        self.view.window().run_command('tutkain_interrupt_evaluation')
        time.sleep(self.delay)

        self.assertRegex(
            self.output_panel_content(),
            r'.*Execution error .*InterruptedException\).*'
        )


class TestExpandSelectionCommand(ViewTestCase):
    def expand(self):
        self.view.run_command('tutkain_expand_selection')

    def test_before_lparen(self):
        self.append_to_view('(foo)')
        self.add_cursors(0)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_after_lparen(self):
        self.append_to_view('(foo)')
        self.add_cursors(1)
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_before_rparen(self):
        self.append_to_view('(foo)')
        self.add_cursors(4)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_after_rparen(self):
        self.append_to_view('(foo)')
        self.add_cursors(6)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_before_lbracket(self):
        self.append_to_view('[foo]')
        self.add_cursors(0)
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_after_lbracket(self):
        self.append_to_view('[foo]')
        self.add_cursors(1)
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_after_rbracket(self):
        self.append_to_view('[foo]')
        self.add_cursors(6)
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_before_lcurly(self):
        self.append_to_view('{:a 1}')
        self.add_cursors(0)
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    @skip('Clojures')
    def test_after_lcurly(self):
        self.append_to_view('{:a 1}')
        self.add_cursors(1)
        self.expand()
        self.assertEquals(self.selection(0), ':a')

    def test_after_rcurly(self):
        self.append_to_view('{:a 1}')
        self.add_cursors(7)
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    def test_before_set(self):
        self.append_to_view('#{1}')
        self.add_cursors(0)
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_set_hash_and_bracket(self):
        self.append_to_view('#{1}')
        self.add_cursors(1)
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_on_symbol(self):
        self.append_to_view('(inc 1)')
        self.add_cursors(2)
        self.expand()
        self.assertEquals(self.selection(0), 'inc')

    def test_before_at(self):
        self.append_to_view('@(foo)')
        self.add_cursors(0)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at(self):
        self.append_to_view('@(foo)')
        self.add_cursors(1)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at_rparen(self):
        self.append_to_view('@(foo)')
        self.add_cursors(6)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_before_quoted_list(self):
        self.append_to_view('\'(foo)')
        self.add_cursors(0)
        self.expand()
        self.assertEquals(self.selection(0), '\'(foo)')

    def test_after_quoted_list(self):
        self.append_to_view('\'(foo)')
        self.add_cursors(6)
        self.expand()
        self.assertEquals(self.selection(0), '\'(foo)')

    def test_nested(self):
        self.append_to_view('(foo (bar))')
        self.add_cursors(5)
        self.expand()
        self.assertEquals(self.selection(0), '(bar)')
        self.expand()
        self.assertEquals(self.selection(0), '(foo (bar))')
