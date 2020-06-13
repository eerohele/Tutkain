from . import sexp


# Should we look for the first (ns) in the view or the last? I guess looking for the last (ns) would
# be the right thing to do, but that might potentially take a long time if the file is long. The
# (ns) will be at the top of the file in probably 99% of the cases, anyway.
def find_declaration(view):
    point = 0
    max_point = view.size()

    while point < max_point:
        element = sexp.find_next_element(view, point)

        if element:
            first = sexp.find_next_element(view, element.begin() + 1)

            if first and view.substr(first) in {'ns', 'in-ns'}:
                second = sexp.find_next_element(view, first.end())

                if second:
                    if view.match_selector(second.begin(), 'keyword.operator.macro'):
                        ns = sexp.find_next_element(view, second.end())
                    else:
                        ns = second

                    symbol = sexp.extract_symbol(view, ns.begin())
                    return view.substr(symbol).replace('\'', '')
            else:
                point = element.end()
        else:
            return None
