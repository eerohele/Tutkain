from . import sexp


def find_regions(view):
    return view.find_by_selector("entity.name.namespace.clojure")


def name(view):
    if regions := find_regions(view):
        return view.substr(regions[0])


def forms(view):
    regions = find_regions(view)

    for region in regions:
        if outermost := sexp.outermost(view, region.begin()):
            yield outermost.extent()
