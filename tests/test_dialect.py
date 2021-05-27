from Tutkain.api import edn
from Tutkain.src import dialects

from .util import ViewTestCase


class TestViewDialect(ViewTestCase):
    def test_get_view_dialect(self):
        self.view.assign_syntax("Packages/Tutkain/Clojure (Tutkain).sublime-syntax")
        self.assertEquals(edn.Keyword("clj"), dialects.for_view(self.view))
        self.view.assign_syntax("Packages/Tutkain/ClojureScript (Tutkain).sublime-syntax")
        self.assertEquals(edn.Keyword("cljs"), dialects.for_view(self.view))
        self.view.assign_syntax("Packages/Tutkain/Clojure Common (Tutkain).sublime-syntax")
        self.assertEquals(edn.Keyword("clj"), dialects.for_view(self.view))
        self.view.window().settings().set("tutkain_evaluation_dialect", "cljs")
        self.assertEquals(edn.Keyword("cljs"), dialects.for_view(self.view))
        self.view.window().settings().set("tutkain_evaluation_dialect", "clj")
        self.assertEquals(edn.Keyword("clj"), dialects.for_view(self.view))


class TestPointDialect(ViewTestCase):
    def test_get_point_dialect(self):
        self.view.assign_syntax("Packages/Tutkain/Clojure (Tutkain).sublime-syntax")
        self.set_view_content("""(Integer/parseInt "42")""")
        self.assertEqual(edn.Keyword("clj"), dialects.for_point(self.view, 0))
        self.view.assign_syntax("Packages/Tutkain/ClojureScript (Tutkain).sublime-syntax")
        self.set_view_content("""(js/parseInt "42")""")
        self.assertEqual(edn.Keyword("cljs"), dialects.for_point(self.view, 0))
        self.view.assign_syntax("Packages/Tutkain/Clojure Common (Tutkain).sublime-syntax")
        self.set_view_content("""(inc 1)""")
        self.assertEqual(edn.Keyword("clj"), dialects.for_point(self.view, 0))
        self.view.assign_syntax("Packages/Markdown/Markdown.sublime-syntax")
        self.set_view_content("""# Hello, world!""")
        self.assertEqual(None, dialects.for_point(self.view, 0))
