def find_declaration(view):
    regions = view.find_by_selector('entity.name.namespace.clojure')
    return regions and view.substr(regions[-1])
