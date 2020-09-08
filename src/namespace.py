def find_last(view):
    regions = view.find_by_selector("entity.name.namespace.clojure")
    return regions and regions[-1]


def find_declaration(view):
    region = find_last(view)
    return region and view.substr(region)
