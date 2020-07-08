import sublime
import time

from unittest import skip
from .util import ViewTestCase
from tutkain import tutkain


class TestCommands(ViewTestCase):
    delay = 0.25

    @classmethod
    def setUpClass(self):
        super().setUpClass()

        self.view.window().run_command(
            'tutkain_connect',
            {'host': 'localhost', 'port': 1234}
        )

    def view_content(self):
        view = tutkain.view_registry.get(self.view.window().id())

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
        self.view.window().run_command('tutkain_clear_output_view')

    def test_evaluate_form(self):
        content = '(+ 1 2)'
        self.set_view_content(content)
        self.set_selections((0, 0))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            self.view_content(),
            '''=> (+ 1 2)\n3\n'''
        )

    def test_evaluate_view(self):
        content = '''(ns app.core) (defn square [x] (* x x)) (comment (square 2))'''
        self.set_view_content(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertEquals(self.view_content(), '')

        self.set_selections((49, 59))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            self.view_content(),
            '''app.core=> (square 2)\n4\n'''
        )

    def test_evaluate_form_before_view(self):
        content = '''(remove-ns 'foo.bar) (ns foo.bar) (defn square [x] (* x x)) (comment (square 2))'''
        self.set_view_content(content)
        self.set_selections((69, 79))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            '''foo.bar=> (square 2)\n:namespace-not-found\n''',
            self.view_content()
        )

    def test_evaluate_form_switch_views(self):
        view_1 = '''(ns baz.quux) (defn plus [x y] (+ x y)) (comment (plus 1 2))'''
        self.set_view_content(view_1)
        self.view.run_command('tutkain_evaluate_view')
        self.set_selections((49, 59))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            '''baz.quux=> (plus 1 2)\n3\n''',
            self.view_content()
        )

        self.view.window().run_command('tutkain_clear_output_view')

        view_2 = '''(ns qux.zot) (defn minus [x y] (- x y)) (comment (minus 4 3))'''
        self.set_view_content(view_2)
        self.view.run_command('tutkain_evaluate_view')
        self.set_selections((49, 60))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            '''qux.zot=> (minus 4 3)\n1\n''',
            self.view_content()
        )

        self.view.window().run_command('tutkain_clear_output_view')

        # Don't need to evaluate view 1 again to evaluate (plus)
        self.set_view_content(view_1)
        self.set_selections((49, 59))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            '''baz.quux=> (plus 1 2)\n3\n''',
            self.view_content()
        )

    def test_evaluate_view_with_error(self):
        content = '''(ns app.core) (inc "a")'''
        self.set_view_content(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertRegex(
            self.view_content(),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

        self.assertRegex(
            self.view_content(),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

    def test_run_test_in_current_namespace(self):
        content = '''(ns mytest.core-test
        (:require [clojure.test :refer [deftest is]]))

        (deftest ok (is (=  2 (+ 1 1))))
        (deftest nok (is (=  3 (+ 1 1))))
        '''
        self.set_view_content(content)
        self.view.run_command('tutkain_run_tests_in_current_namespace')
        time.sleep(self.delay)

        self.assertEquals(
            self.view_content().splitlines()[-1],
            '''{:test 2, :pass 1, :fail 1, :error 0}'''
        )

    def test_run_test_in_current_namespace_with_error(self):
        content = '''(ns error.core-test
        (:require [clojure.test :refer [deftest is]]))

        (deftest test-with-error (is (= "JavaScript" (+ 1 "a"))))
        '''
        self.set_view_content(content)
        self.view.run_command('tutkain_run_tests_in_current_namespace')
        time.sleep(self.delay)

        self.assertEquals(
            self.view_content().splitlines()[-1],
            '''{:test 1, :pass 0, :fail 0, :error 1}'''
        )

    # TODO: Figure out how to test EvaluateInputCommand

    def test_interrupt_evaluation(self):
        content = '''(do (Thread/sleep 1000) (println "Boom!"))'''
        self.set_view_content(content)
        self.set_selections((0, 0))
        self.view.run_command('tutkain_evaluate_form')
        self.view.window().run_command('tutkain_interrupt_evaluation')
        time.sleep(self.delay)

        self.assertRegex(
            self.view_content(),
            r'.*Execution error .*InterruptedException\).*'
        )
