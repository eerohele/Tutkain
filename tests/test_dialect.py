from Tutkain.api import edn
from Tutkain.src import dialects

from .util import ViewTestCase


class TestDialect(ViewTestCase):
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
