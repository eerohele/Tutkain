import sublime

from ...api import edn
from . import info


def goto(window, items, index):
    if index != -1:
        item = items[index]
        info.goto(window, info.parse_location(item))


def handle_response(window, kinds, response):
    items = []

    if vars := response.get(edn.Keyword("vars")):
        for var in vars:
            name = "/".join([var.get(edn.Keyword("ns")), var.get(edn.Keyword("name")).name])

            doc = var.get(edn.Keyword("doc"), "")

            if "\n" in doc:
                docstring = var.get(edn.Keyword("doc")).split("\n")[0] + "…"
            else:
                docstring = doc

            arglists = " ".join(var.get(edn.Keyword("arglists"), []))

            if type := var.get(edn.Keyword("type")):
                kind = kinds.get(type.name, sublime.KIND_AMBIGUOUS)
            else:
                kind = sublime.KIND_AMBIGUOUS

            item = sublime.QuickPanelItem(name, details=docstring, annotation=arglists, kind=kind)
            items.append(item)

        if symbol := response.get(edn.Keyword("symbol")):
            selected_index = list(map(lambda v: v.get(edn.Keyword("name")), vars)).index(edn.Symbol(symbol))
        else:
            selected_index = -1

        window.show_quick_panel(
            items,
            lambda index: goto(window, vars, index),
            selected_index=selected_index
        )
