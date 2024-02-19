from typing import Union

from sublime import View

from ..api import edn

DIALECT_NAMES = edn.kwmap(
    {
        "clj": "Clojure",
        "cljs": "ClojureScript",
        "cljc": "Clojure Common",
        "bb": "Babashka",
    }
)


SYNTAXES = {
    edn.Keyword("clj"): "Packages/Tutkain/Clojure (Tutkain).sublime-syntax",
    edn.Keyword("cljs"): "Packages/Tutkain/ClojureScript (Tutkain).sublime-syntax",
}


DIALECTS = {
    edn.Keyword("clj"): ".clj",
    edn.Keyword("cljs"): ".cljs",
    edn.Keyword("cljc"): ".cljc",
    edn.Keyword("bb"): ".bb",
}


def extension(dialect):
    return DIALECTS.get(dialect, ".clj")


def syntax(view):
    return SYNTAXES.get(for_view(view))


def name(dialect: edn.Keyword) -> str:
    return DIALECT_NAMES.get(dialect, "")


def evaluation_dialect(view: Union[View, None]) -> Union[edn.Keyword, None]:
    """Given a Tutkain REPL view, return the evaluation dialect for the
    window the view belongs to."""
    if (
        view
        and (window := view.window())
        and (dialect := window.settings().get("tutkain_evaluation_dialect"))
    ):
        return edn.Keyword(dialect)


def for_point(view: View, point: int) -> Union[edn.Keyword, None]:
    if view.match_selector(point, "source.clojure.clojure-common"):
        return evaluation_dialect(view) or edn.Keyword("clj")
    if view.match_selector(point, "source.clojure.clojurescript"):
        return edn.Keyword("cljs")
    if view.match_selector(point, "source.clojure.babashka"):
        return edn.Keyword("bb")
    if view.match_selector(point, "source.clojure") and evaluation_dialect(
        view
    ) == edn.Keyword("bb"):
        return edn.Keyword("bb")
    if view.match_selector(point, "source.clojure"):
        return edn.Keyword("clj")


def for_view(view):
    if syntax := view.syntax():
        if syntax.scope == "source.clojure.clojure-common":
            return evaluation_dialect(view) or edn.Keyword("clj")
        if syntax.scope == "source.clojure.clojurescript":
            return edn.Keyword("cljs")
        if syntax.scope == "source.clojure.babashka":
            return edn.Keyword("bb")
        if syntax.scope == "source.clojure" and evaluation_dialect(view) == edn.Keyword(
            "bb"
        ):
            return edn.Keyword("bb")
        if syntax.scope == "source.clojure":
            return edn.Keyword("clj")
