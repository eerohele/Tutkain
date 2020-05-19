import sublime
import time

from tutkain import tutkain
from unittest import TestCase


def append_to_view(view, chars):
    view.run_command('append', {'characters': chars})


def move_cursor(view, pos):
    view.sel().clear()
    view.sel().add(sublime.Region(pos))


class TestEvaluateViewCommand(TestCase):
    delay = 0.15

    @classmethod
    def setUpClass(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.assign_syntax('Packages/Clojure/Clojure.sublime-syntax')

        self.view.window().run_command(
            'tutkain_connect',
            {'host': 'localhost', 'port': 1234}
        )

        self.output_panel = self.view.window().find_output_panel('tutkain')

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('tutkain_disconnect')
            self.view.window().destroy_output_panel('tutkain')
            self.view.window().run_command('close_file')

    def setUp(self):
        self.view.run_command('select_all')
        self.view.run_command('right_delete')
        self.view.window().run_command('tutkain_clear_output_panel')

    def test_evaluate_form(self):
        content = '(+ 1 2)'
        append_to_view(self.view, content)
        move_cursor(self.view, 0)
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            tutkain.region_content(self.output_panel),
            ''';; => (+ 1 2)\n3\n'''
        )

    def test_evaluate_view(self):
        content = '''(ns app.core) (defn square [x] (* x x))'''
        append_to_view(self.view, content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertEquals(
            tutkain.region_content(self.output_panel),
            ''';; Loading view...\n'''
        )

        append_to_view(self.view, ' (square 2)')
        move_cursor(self.view, 40)
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            tutkain.region_content(self.output_panel),
            ''';; Loading view...
;; => (square 2)
4
''')

    def test_evaluate_view_with_error(self):
        content = '''(ns app.core) (inc "a")'''
        append_to_view(self.view, content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertRegex(
            tutkain.region_content(self.output_panel),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

    def test_run_test_in_current_namespace(self):
        content = '''(ns app.core-test
        (:require [clojure.test :refer [deftest is]]))

        (deftest ok (is (=  2 (+ 1 1))))
        (deftest nok (is (=  3 (+ 1 1))))
        '''
        append_to_view(self.view, content)
        self.view.run_command('tutkain_run_tests_in_current_namespace')
        time.sleep(self.delay)

        self.assertEquals(
            tutkain.region_content(self.output_panel).splitlines()[-1],
            '''{:test 2, :pass 1, :fail 1, :error 0, :type :summary}'''
        )

    def test_run_test_in_current_namespace_with_error(self):
        content = '''(ns error.core-test
        (:require [clojure.test :refer [deftest is]]))

        (deftest test-with-error (is (= "JavaScript" (+ 1 "a"))))
        '''
        append_to_view(self.view, content)
        self.view.run_command('tutkain_run_tests_in_current_namespace')
        time.sleep(self.delay)

        self.assertRegex(
            tutkain.region_content(self.output_panel),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

    # TODO: Figure out how to test EvaluateInputCommand

    def test_interrupt_evaluation(self):
        content = '''(do (Thread/sleep 1000) (println "Boom!"))'''
        append_to_view(self.view, content)
        move_cursor(self.view, 0)
        self.view.run_command('tutkain_evaluate_form')
        self.view.window().run_command('tutkain_interrupt_evaluation')
        time.sleep(self.delay)

        self.assertRegex(
            tutkain.region_content(self.output_panel),
            r'.*Execution error .*InterruptedException\).*'
        )


class TestBrackets(TestCase):
    @classmethod
    def setUpClass(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        # requires https://github.com/oconnor0/Clojures
        self.view.assign_syntax('Packages/Clojures/Clojure.sublime-syntax')

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
        append_to_view(self.view, '(foo)')
        move_cursor(self.view, 0)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_after_lparen(self):
        append_to_view(self.view, '(foo)')
        move_cursor(self.view, 1)
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_before_rparen(self):
        append_to_view(self.view, '(foo)')
        move_cursor(self.view, 4)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_after_rparen(self):
        append_to_view(self.view, '(foo)')
        move_cursor(self.view, 6)
        self.expand()
        self.assertEquals(self.selection(0), '(foo)')

    def test_before_lbracket(self):
        append_to_view(self.view, '[foo]')
        move_cursor(self.view, 0)
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_after_lbracket(self):
        append_to_view(self.view, '[foo]')
        move_cursor(self.view, 1)
        self.expand()
        self.assertEquals(self.selection(0), 'foo')

    def test_after_rbracket(self):
        append_to_view(self.view, '[foo]')
        move_cursor(self.view, 6)
        self.expand()
        self.assertEquals(self.selection(0), '[foo]')

    def test_before_lcurly(self):
        append_to_view(self.view, '{:a 1}')
        move_cursor(self.view, 0)
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    def test_after_lcurly(self):
        append_to_view(self.view, '{:a 1}')
        move_cursor(self.view, 1)
        self.expand()
        self.assertEquals(self.selection(0), ':a')

    def test_after_rcurly(self):
        append_to_view(self.view, '{:a 1}')
        move_cursor(self.view, 7)
        self.expand()
        self.assertEquals(self.selection(0), '{:a 1}')

    def test_before_set(self):
        append_to_view(self.view, '#{1}')
        move_cursor(self.view, 0)
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_set_hash_and_bracket(self):
        append_to_view(self.view, '#{1}')
        move_cursor(self.view, 1)
        self.expand()
        self.assertEquals(self.selection(0), '#{1}')

    def test_between_on_symbol(self):
        append_to_view(self.view, '(inc 1)')
        move_cursor(self.view, 2)
        self.expand()
        self.assertEquals(self.selection(0), 'inc')

    def test_before_at(self):
        append_to_view(self.view, '@(foo)')
        move_cursor(self.view, 0)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at(self):
        append_to_view(self.view, '@(foo)')
        move_cursor(self.view, 1)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_after_at_rparen(self):
        append_to_view(self.view, '@(foo)')
        move_cursor(self.view, 6)
        self.expand()
        self.assertEquals(self.selection(0), '@(foo)')

    def test_before_quoted_list(self):
        append_to_view(self.view, '\'(foo)')
        move_cursor(self.view, 0)
        self.expand()
        self.assertEquals(self.selection(0), '\'(foo)')

    def test_after_quoted_list(self):
        append_to_view(self.view, '\'(foo)')
        move_cursor(self.view, 6)
        self.expand()
        self.assertEquals(self.selection(0), '\'(foo)')
