import sublime

from ...api import edn
from . import info


def goto(window, view, items, index):
    if index == -1:
        window.focus_view(view)
    else:
        item = items[index]
        info.goto(window, info.parse_location(item), flags=sublime.ADD_TO_SELECTION | sublime.ENCODED_POSITION | sublime.SEMI_TRANSIENT | sublime.REPLACE_MRU | sublime.CLEAR_TO_RIGHT)


def to_quick_panel_items(kinds, results, symbol=None):
    items = []

    for result in results:
        symbol = result.get(edn.Keyword("name"))

        if ns := result.get(edn.Keyword("ns")):
            name = "/".join([ns, symbol.name])
        else:
            name = symbol.name

        docstring = result.get(edn.Keyword("doc"), "")

        if "\n" in docstring:
            docstring = docstring.split("\n")[0] + "…"

        arglists = " ".join(result.get(edn.Keyword("arglists"), []))
        kind = sublime.KIND_AMBIGUOUS

        type = result.get(edn.Keyword("type"))

        if type:
            kind = kinds.get(type.name, sublime.KIND_AMBIGUOUS)

            if type == edn.Keyword("namespace"):
                items.append(sublime.QuickPanelItem(name, details=docstring, kind=kind))
            else:
                items.append(
                    sublime.QuickPanelItem(name, details=docstring, annotation=arglists, kind=kind)
                )

    return items


def handle_response(window, kinds, response):
    results = response.get(edn.Keyword("results"), [])

    items = to_quick_panel_items(kinds, results)

    active_view = window.active_view()

    if symbol := response.get(edn.Keyword("symbol")):
        names = list(map(lambda v: v.get(edn.Keyword("name")), results))

        if symbol in names:
            selected_index = names.index(symbol)
        else:
            selected_index = 0
    else:
        selected_index = -1

    window.show_quick_panel(
        items,
        lambda index: goto(window, active_view, results, index),
        on_highlight=lambda index: goto(window, active_view, results, index),
        selected_index=selected_index
    )
