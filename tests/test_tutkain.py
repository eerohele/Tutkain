import sublime
import time

from unittest import skip, TestCase
from .util import ViewTestCase
from tutkain import tutkain


class TestCommands(ViewTestCase):
    delay = 0.15

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.view.window().run_command(
            'tutkain_connect',
            {'host': 'localhost', 'port': 1234}
        )

    def view_content(self, name):
        view = tutkain.view_registry.get(name)
        if view:
            return view.substr(sublime.Region(0, view.size()))

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('tutkain_disconnect')
            self.view.window().run_command('close_file')
            tutkain.view_registry.clear()

    def setUp(self):
        super().setUp()
        self.view.window().run_command('tutkain_clear_output_views')

    def test_evaluate_form(self):
        content = '(+ 1 2)'
        self.append_to_view(content)
        self.set_selections((0, 0))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            self.view_content('result'),
            '''=> (+ 1 2)\n3\n'''
        )

    def test_evaluate_view(self):
        content = '''(ns app.core) (defn square [x] (* x x))'''
        self.append_to_view(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertEquals(self.view_content('result'), '')

        self.assertEquals(self.view_content('out'), '')

        self.append_to_view(' (square 2)')
        self.set_selections((40, 40))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            self.view_content('result'),
            '''=> (square 2)\n4\n''')

        self.assertEquals(self.view_content('out'), '')

    def test_evaluate_view_with_error(self):
        content = '''(ns app.core) (inc "a")'''
        self.append_to_view(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertRegex(
            self.view_content('result'),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

        self.assertRegex(
            self.view_content('out'),
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
            self.view_content('result').splitlines()[-1],
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
            self.view_content('out'),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

    # TODO: Figure out how to test EvaluateInputCommand

    def test_interrupt_evaluation(self):
        content = '''(do (Thread/sleep 1000) (println "Boom!"))'''
        self.append_to_view(content)
        self.set_selections((0, 0))
        self.view.run_command('tutkain_evaluate_form')
        self.view.window().run_command('tutkain_interrupt_evaluation')
        time.sleep(self.delay)

        self.assertRegex(
            self.view_content('out'),
            r'.*Execution error .*InterruptedException\).*'
        )


class TestExpandSelectionCommand(ViewTestCase):
    def expand(self):
        self.view.run_command('tutkain_expand_selection')

    def test_before_lparen(self):
        self.append_to_view('(foo)')
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_after_lparen(self):
        self.append_to_view('(foo)')
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_before_rparen(self):
        self.append_to_view('(foo)')
        self.set_selections((4, 4))
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_after_rparen(self):
        self.append_to_view('(foo)')
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_before_lbracket(self):
        self.append_to_view('[foo]')
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_after_lbracket(self):
        self.append_to_view('[foo]')
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_after_rbracket(self):
        self.append_to_view('[foo]')
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_before_lcurly(self):
        self.append_to_view('{:a 1}')
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    @skip('Clojures')
    def test_after_lcurly(self):
        self.append_to_view('{:a 1}')
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(self.selection(0), ':a')

    def test_after_rcurly(self):
        self.append_to_view('{:a 1}')
        self.set_selections((7, 7))
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    def test_before_set(self):
        self.append_to_view('#{1}')
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_set_hash_and_bracket(self):
        self.append_to_view('#{1}')
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_on_symbol(self):
        self.append_to_view('(inc 1)')
        self.set_selections((2, 2))
        self.expand()
        self.assertEquals(self.selection(0), 'inc')

    def test_before_at(self):
        self.append_to_view('@(foo)')
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at(self):
        self.append_to_view('@(foo)')
        self.set_selections((1, 1))
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at_rparen(self):
        self.append_to_view('@(foo)')
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_before_quoted_list(self):
        self.append_to_view('\'(foo)')
        self.set_selections((0, 0))
        self.expand()
        self.assertEquals(self.selection(0), '\'(foo)')

    def test_after_quoted_list(self):
        self.append_to_view('\'(foo)')
        self.set_selections((6, 6))
        self.expand()
        self.assertEquals(self.selection(0), '\'(foo)')

    def test_nested(self):
        self.append_to_view('(foo (bar))')
        self.set_selections((5, 5))
        self.expand()
        self.assertEquals(self.selection(0), '(bar)')
        self.expand()
        self.assertEquals(self.selection(0), '(foo (bar))')
