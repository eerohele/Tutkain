from ..api import edn
from . import state


DIALECT_NAMES = edn.kwmap({
    "clj": "Clojure",
    "cljs": "ClojureScript",
    "cljc": "Clojure Common",
})


def name(dialect):
    return DIALECT_NAMES.get(dialect)


def focus_view(view, dialect):
    """Given an initial view and a dialect, focus the active REPL view for
    that dialect, then focus the initial view."""
    # Focus the REPL view for the given dialect
    view.window().focus_view(state.repl_view(view.window(), dialect))
    # Focus the view that was initially active
    view.window().focus_view(view)
