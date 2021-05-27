from ..api import edn
from . import state
from .repl import views


DIALECT_NAMES = edn.kwmap({
    "clj": "Clojure",
    "cljs": "ClojureScript",
    "cljc": "Clojure Common",
    "bb": "Babashka"
})


def name(dialect: edn.Keyword) -> str:
    return DIALECT_NAMES.get(dialect, "")


def for_point(view, point):
    if view.match_selector(point, "source.clojure.clojure-common") and (
        eval_dialect := view.window().settings().get(
            "tutkain_evaluation_dialect"
        )
    ):
        return edn.Keyword(eval_dialect)
    if view.match_selector(point, "source.clojure.clojurescript"):
        return edn.Keyword("cljs")
    if view.match_selector(point, "source.clojure.babashka"):
        return edn.Keyword("bb")

    return edn.Keyword("clj")


def for_view(view):
    if syntax := view.syntax():
        if syntax.scope == "source.clojure.clojure-common":
            return edn.Keyword(view.window().settings().get(
                "tutkain_evaluation_dialect",
                "clj"
            ))
        if syntax.scope == "source.clojure.clojurescript":
            return edn.Keyword("cljs")
        if syntax.scope == "source.clojure.babashka":
            return edn.Keyword("bb")
        if syntax.scope == "source.clojure":
            return edn.Keyword("clj")


def focus_view(view: View, dialect: edn.Keyword) -> None:
    """Given an initial view and a dialect, if the currently active REPL view
    has a different dialect than the given dialect, focus the active REPL view
    for the given dialect, then refocus the initial view."""
    if (window := view.window()) and (
        active_repl_view := views.active_repl_view(window)
    ) and views.get_dialect(active_repl_view) != dialect:
        # Focus the REPL view for the given dialect
        window.focus_view(state.repl_view(window, dialect))
        # Focus the view that was initially active
        window.focus_view(view)
