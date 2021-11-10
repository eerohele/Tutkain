import sublime

from ...api import edn
from . import info


def goto(window, items, index):
    if index != -1:
        item = items[index]
        info.goto(window, info.parse_location(item))


def handle_response(window, kinds, response):
    items = []
    results = response.get(edn.Keyword("results"), [])

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
                items.append(sublime.QuickPanelItem(name, kind=kind))
            else:
                items.append(
                    sublime.QuickPanelItem(name, details=docstring, annotation=arglists, kind=kind)
                )

    if symbol := response.get(edn.Keyword("symbol")):
        selected_index = list(
            map(lambda v: v.get(edn.Keyword("name")), results)
        ).index(edn.Symbol(symbol))
    else:
        selected_index = -1

    window.show_quick_panel(
        items,
        lambda index: goto(window, results, index),
        selected_index=selected_index
    )
