from inspect import cleandoc
import sublime
import os

from .util import ViewTestCase, wait_until_contains
from Tutkain.src.repl import tap
from Tutkain.src import test
from Tutkain import package as tutkain


HOST = os.getenv("NREPL_HOST", "localhost")


class TestCommands(ViewTestCase):
    @classmethod
    def content(self, view):
        return view and view.substr(sublime.Region(0, view.size()))

    @classmethod
    def repl_view_content(self):
        if "active_repl_view" in tutkain.state:
            view = tutkain.get_active_repl_view(self.view.window())
            return view.substr(sublime.Region(0, view.size()))

    @classmethod
    def connect(self):
        self.view.window().run_command("tutkain_connect", {"host": HOST, "port": 1234})

        if not wait_until_contains(
            """Clojure 1.10.1\nnREPL 0.8.2\n""",
            lambda: self.content(tutkain.get_active_repl_view(self.view.window())),
            delay=1,
        ):
            raise AssertionError("REPL did not respond in time.")

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.connect()

    @classmethod
    def tearDownClass(self):
        view = tutkain.get_active_repl_view(self.view.window())
        view and view.close()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.view.window().run_command("tutkain_clear_output_view")

    def test_evaluate_form(self):
        content = "(+ 1 2)"
        self.set_view_content(content)
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate_form")
        self.assertEqualsEventually("""user=> (+ 1 2)\n3\n""", self.repl_view_content)

    def test_evaluate_view(self):
        content = """(ns app.core) (defn square [x] (* x x)) (comment (square 2))"""
        self.set_view_content(content)
        self.view.run_command("tutkain_evaluate_view")

        self.assertEqualsEventually(":tutkain/loaded\n", self.repl_view_content)

        self.set_selections((49, 59))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """:tutkain/loaded\napp.core=> (square 2)\n4\n""", self.repl_view_content
        )

    def test_evaluate_form_before_view(self):
        content = """(ns my.ns (:require [clojure.set :as set]))

(defn x [y z] (set/subset? y z))

(x #{1} #{1 2})"""

        self.set_view_content(content)
        self.set_selections((45, 45))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """my.ns=> (defn x [y z] (set/subset? y z))\n#'my.ns/x\n""",
            self.repl_view_content,
        )

        self.set_selections((79, 79))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """my.ns=> (defn x [y z] (set/subset? y z))\n#'my.ns/x\nmy.ns=> (x #{1} #{1 2})\ntrue\n""",
            self.repl_view_content,
        )

    def test_evaluate_form_switch_views(self):
        view_1 = """(ns baz.quux) (defn plus [x y] (+ x y)) (comment (plus 1 2))"""
        self.set_view_content(view_1)
        self.view.run_command("tutkain_evaluate_view")
        self.assertContainsEventually(":tutkain/loaded\n", self.repl_view_content)

        self.set_selections((49, 59))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """:tutkain/loaded\nbaz.quux=> (plus 1 2)\n3\n""", self.repl_view_content
        )

        self.view.window().run_command("tutkain_clear_output_view")

        view_2 = """(ns qux.zot) (defn minus [x y] (- x y)) (comment (minus 4 3))"""
        self.set_view_content(view_2)
        self.view.run_command("tutkain_evaluate_view")
        self.assertContainsEventually(":tutkain/loaded\n", self.repl_view_content)

        self.set_selections((49, 60))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """:tutkain/loaded\nqux.zot=> (minus 4 3)\n1\n""", self.repl_view_content
        )

        self.view.window().run_command("tutkain_clear_output_view")

        # Don't need to evaluate view 1 again to evaluate (plus)
        self.set_view_content(view_1)
        self.set_selections((49, 59))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """baz.quux=> (plus 1 2)\n3\n""", self.repl_view_content
        )

    def test_evaluate_view_with_error(self):
        content = """(ns app.core) (inc "a")"""
        self.set_view_content(content)
        self.view.run_command("tutkain_evaluate_view")

        self.assertMatchesEventually(
            r".*class java.lang.String cannot be cast to class java.lang.Number.*",
            self.repl_view_content,
        )

        self.assertMatchesEventually(
            r".*class java.lang.String cannot be cast to class java.lang.Number.*",
            self.repl_view_content,
        )

    def test_run_test_in_current_namespace(self):
        content = """(ns mytest.core-test
  (:require [clojure.test :refer [deftest is]]))

(deftest ok (is (=  2 (+ 1 1))))
(deftest nok (is (=  3 (+ 1 1))))
        """
        self.set_view_content(content)
        self.view.run_command("tutkain_run_tests_in_current_namespace")

        self.assertContainsEventually(
            """{:test 2, :pass 1, :fail 1, :error 0, :type :summary}""",
            self.repl_view_content,
        )

        self.assertEquals([sublime.Region(71, 71)], test.regions(self.view, "passes"))
        self.assertEquals(
            [sublime.Region(104, 104)], test.regions(self.view, "failures")
        )
        self.assertEquals([], test.regions(self.view, "errors"))

    def test_run_test_in_current_namespace_with_error(self):
        content = """(ns error.core-test
        (:require [clojure.test :refer [deftest is]]))

        (deftest test-with-error (is (= "JavaScript" (+ 1 "a"))))
        """
        self.set_view_content(content)
        self.view.run_command("tutkain_run_tests_in_current_namespace")

        self.assertContainsEventually(
            """{:test 1, :pass 0, :fail 0, :error 1, :type :summary}""",
            self.repl_view_content,
        )

    def test_run_test_under_cursor(self):
        content = """(ns mytest.core-test
  (:require [clojure.test :refer [deftest is]]))

(deftest ok (is (=  2 (+ 1 1))))
(deftest nok (is (=  3 (+ 1 1))))
        """
        self.set_view_content(content)
        self.set_selections((71, 71))
        self.view.run_command("tutkain_run_test_under_cursor")

        self.assertEqualsEventually(
            [sublime.Region(71, 71)], lambda: test.regions(self.view, "passes")
        )

        self.assertEquals([], test.regions(self.view, "failures"))
        self.assertEquals([], test.regions(self.view, "errors"))

        self.set_selections((104, 104))
        self.view.run_command("tutkain_run_test_under_cursor")

        self.assertEqualsEventually(
            [sublime.Region(104, 104)], lambda: test.regions(self.view, "failures")
        )

        self.assertEquals([], test.regions(self.view, "passes"))
        self.assertEquals([], test.regions(self.view, "errors"))

    # TODO: Figure out how to test EvaluateInputCommand

    def test_interrupt_evaluation(self):
        content = """(do (Thread/sleep 10000) (println "Boom!"))"""
        self.set_view_content(content)
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """user=> (do (Thread/sleep 10000) (println "Boom!"))\n""",
            self.repl_view_content,
        )

        self.view.window().run_command("tutkain_interrupt_evaluation")

        self.assertMatchesEventually(
            r".*Execution error .*InterruptedException\).*", self.repl_view_content
        )

    def test_multiple_repl_views(self):
        initial_repl_view = tutkain.get_active_repl_view(self.view.window())

        content = cleandoc(
            """
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
        """
        )

        self.set_view_content(content)

        self.view.run_command("tutkain_evaluate_view")

        self.assertContainsEventually(
            ":tutkain/loaded\n", lambda: self.content(initial_repl_view)
        )

        self.set_selections((80, 90))

        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """:tutkain/loaded
app.core=> (square 2)
4\n""",
            lambda: self.content(initial_repl_view),
        )

        self.connect()
        other_repl_view = tutkain.get_active_repl_view(self.view.window())

        self.set_selections((93, 103))
        self.view.run_command("tutkain_evaluate_form")

        self.assertContainsEventually(
            """Clojure 1.10.1
nREPL 0.8.2
app.core=> (square 4)
16\n""",
            lambda: self.content(other_repl_view),
        )

        # Initial REPL view content remains the same
        self.assertContainsEventually(
            """:tutkain/loaded
app.core=> (square 2)
4\n""",
            lambda: self.content(initial_repl_view),
        )

        # Evaluate (tap> ,,,)
        self.set_selections((106, 123))
        self.view.run_command("tutkain_evaluate_form")

        client = tutkain.state["client_by_view"][initial_repl_view.id()]
        panel = tap.find_panel(self.view.window(), client)

        # Tap is in the tap panel only once
        self.assertEqualsEventually("64\n", lambda: self.content(panel))

        self.view.window().focus_view(initial_repl_view)
        self.view.window().focus_view(self.view)
        self.set_selections((93, 103))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEqualsEventually(
            """Clojure 1.10.1
nREPL 0.8.2
app.core=> (square 4)
16
app.core=> (tap> (square 8))
true\n""",
            lambda: self.content(other_repl_view),
        )

        self.assertEqualsEventually(
            """:tutkain/loaded
app.core=> (square 2)
4
app.core=> (square 4)
16\n""",
            lambda: self.content(initial_repl_view),
        )


class TestBabashka(ViewTestCase):
    @classmethod
    def content(self, view):
        return view and view.substr(sublime.Region(0, view.size()))

    @classmethod
    def repl_view_content(self):
        if "active_repl_view" in tutkain.state:
            view = tutkain.get_active_repl_view(self.view.window())
            return view.substr(sublime.Region(0, view.size()))

    @classmethod
    def connect(self):
        self.view.window().run_command("tutkain_connect", {"host": HOST, "port": 1667})

        if not wait_until_contains(
            """Babashka 0.2.2\nbabashka.nrepl 0.0.4-SNAPSHOT\n""",
            lambda: self.content(tutkain.get_active_repl_view(self.view.window())),
            delay=1,
        ):
            raise AssertionError("REPL did not respond in time.")

    @classmethod
    def setUpClass(self):
        super().setUpClass()
        self.connect()

    @classmethod
    def tearDownClass(self):
        view = tutkain.get_active_repl_view(self.view.window())
        view and view.close()
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.view.window().run_command("tutkain_clear_output_view")

    def test_evaluate_form(self):
        content = "(+ 1 2)"
        self.set_view_content(content)
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate_form")
        self.assertEqualsEventually("""user=> (+ 1 2)\n3\n""", self.repl_view_content)
