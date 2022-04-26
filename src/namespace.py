from . import sexp
from ..api import edn


def find_regions(view):
    return view.find_by_selector("meta.sexp entity.name.namespace.clojure - (meta.sexp meta.sexp)")


def name(view):
    if regions := find_regions(view):
        return view.substr(regions[0])


def forms(view):
    regions = find_regions(view)

    for region in regions:
        if outermost := sexp.outermost(view, region.begin()):
            yield outermost.extent()


def default(dialect):
    return "cljs.user" if dialect == edn.Keyword("cljs") else "user"


def name_or_default(view, dialect):
    return name(view) or default(dialect)
