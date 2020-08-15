from inspect import cleandoc
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
        self.view.window().run_command('tutkain_connect', {'host': 'localhost', 'port': 1234})
        time.sleep(2.5)

    def repl_view_content(self):
        if 'active_repl_view' in tutkain.state:
            view = tutkain.get_active_repl_view()
            return view.substr(sublime.Region(0, view.size()))

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command('tutkain_disconnect')
            self.view.window().run_command('close_file')

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
            self.repl_view_content(),
            '''user=> (+ 1 2)\n3\n'''
        )

    def test_evaluate_view(self):
        content = '''(ns app.core) (defn square [x] (* x x)) (comment (square 2))'''
        self.set_view_content(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertEquals(self.repl_view_content(), '')

        self.set_selections((49, 59))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            self.repl_view_content(),
            '''app.core=> (square 2)\n4\n'''
        )

    def test_evaluate_form_before_view(self):
        content = '''(remove-ns 'foo.bar) (ns foo.bar) (defn square [x] (* x x)) (comment (square 2))'''
        self.set_view_content(content)
        self.set_selections((69, 79))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            '''foo.bar=> (square 2)\n:tutkain/namespace-not-found\n''',
            self.repl_view_content()
        )

    def test_evaluate_form_switch_views(self):
        view_1 = '''(ns baz.quux) (defn plus [x y] (+ x y)) (comment (plus 1 2))'''
        self.set_view_content(view_1)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.set_selections((49, 59))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            '''baz.quux=> (plus 1 2)\n3\n''',
            self.repl_view_content()
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
            self.repl_view_content()
        )

        self.view.window().run_command('tutkain_clear_output_view')

        # Don't need to evaluate view 1 again to evaluate (plus)
        self.set_view_content(view_1)
        self.set_selections((49, 59))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals(
            '''baz.quux=> (plus 1 2)\n3\n''',
            self.repl_view_content()
        )

    def test_evaluate_view_with_error(self):
        content = '''(ns app.core) (inc "a")'''
        self.set_view_content(content)
        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.assertRegex(
            self.repl_view_content(),
            r'.*class java.lang.String cannot be cast to class java.lang.Number.*'
        )

        self.assertRegex(
            self.repl_view_content(),
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
            self.repl_view_content().splitlines()[-1],
            '''{:test 2, :pass 1, :fail 1, :error 0, :type :summary}'''
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
            self.repl_view_content().splitlines()[-1],
            '''{:test 1, :pass 0, :fail 0, :error 1, :type :summary}'''
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
            self.repl_view_content(),
            r'.*Execution error .*InterruptedException\).*'
        )


class TestMultipleReplViews(ViewTestCase):
    delay = 0.25

    def content(self, view):
        return view.substr(sublime.Region(0, view.size()))

    def setUp(self):
        super().setUp()
        self.view.window().run_command('tutkain_clear_output_view')

    def tearDown(self):
        super().tearDown()

        if self.view:
            window = self.view.window()
            window.run_command('tutkain_disconnect')
            window.run_command('tutkain_disconnect')

    def test_evaluate(self):
        self.view.window().run_command('tutkain_connect', {'host': 'localhost', 'port': 1234})
        repl_view_1 = tutkain.get_active_repl_view()

        content = cleandoc('''
        (remove-ns 'app.core)

        (ns app.core)

        (defn square
          [x]
          (* x x))

        (comment
          (square 2)
          (square 4)
          (tap> (square 8))
          )
        ''')

        self.set_view_content(content)

        self.view.run_command('tutkain_evaluate_view')
        time.sleep(self.delay)

        self.set_selections((80, 90))

        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals('''Clojure 1.10.1
nREPL 0.8.0
:tutkain/ready
app.core=> (square 2)
4\n''', self.content(repl_view_1))

        self.view.window().run_command('tutkain_connect', {'host': 'localhost', 'port': 1234})
        time.sleep(self.delay)
        repl_view_2 = tutkain.get_active_repl_view()

        self.set_selections((93, 103))

        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals('''Clojure 1.10.1
nREPL 0.8.0
:tutkain/ready
app.core=> (square 4)
16\n''', self.content(repl_view_2))

        # REPL view 1 content remains the same
        self.assertEquals('''Clojure 1.10.1
nREPL 0.8.0
:tutkain/ready
app.core=> (square 2)
4\n''', self.content(repl_view_1))

        # Evaluate (tap> ,,,)
        self.set_selections((106, 123))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        panel = self.view.window().find_output_panel('tutkain')

        # Tap is in the tap panel only once
        self.assertEquals('64\n', self.content(panel))

        self.view.window().focus_view(repl_view_1)
        self.view.window().focus_view(self.view)
        self.set_selections((93, 103))
        self.view.run_command('tutkain_evaluate_form')
        time.sleep(self.delay)

        self.assertEquals('''Clojure 1.10.1
nREPL 0.8.0
:tutkain/ready
app.core=> (square 4)
16
app.core=> (tap> (square 8))
true\n''', self.content(repl_view_2))

        self.assertEquals('''Clojure 1.10.1
nREPL 0.8.0
:tutkain/ready
app.core=> (square 2)
4
app.core=> (square 4)
16\n''', self.content(repl_view_1))
