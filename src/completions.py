import sublime
from . import state
from . import dialects
from . import selectors
from . import namespace
from ..api import edn


KINDS = {
    "function": sublime.KIND_FUNCTION,
    "var": sublime.KIND_VARIABLE,
    "macro": (sublime.KIND_ID_FUNCTION, "m", "Macro"),
    "multimethod": (sublime.KIND_ID_FUNCTION, "u", "Multimethod"),
    "namespace": sublime.KIND_NAMESPACE,
    "field": sublime.KIND_VARIABLE,
    "class": sublime.KIND_TYPE,
    "special-form": (sublime.KIND_ID_FUNCTION, "s", "Special form"),
    "method": (sublime.KIND_ID_FUNCTION, "i", "Instance method"),
    "static-method": (sublime.KIND_ID_FUNCTION, "c", "Static method"),
    "keyword": sublime.KIND_KEYWORD,
    "protocol": sublime.KIND_TYPE
}


def completion_item(item):
    details = ""

    if klass := item.get(edn.Keyword("class")):
        details = f"on <code>{klass}</code>"

        if return_type := item.get(edn.Keyword("return-type")):
            details += f", returns <code>{return_type}</code>"
    elif edn.Keyword("doc") in item:
        d = {}

        for k, v in item.items():
            d[k.name] = v.name if isinstance(v, edn.Keyword) else v

        details = f"""<a href="{sublime.command_url("tutkain_show_popup", args={"item": d})}">More</a>"""

    candidate = item.get(edn.Keyword("candidate"))
    trigger = candidate + " "
    type = item.get(edn.Keyword("type"))

    arglists = item.get(edn.Keyword("arglists"), [])
    annotation = ""

    if type in {edn.Keyword("method"), edn.Keyword("static-method")}:
        annotation = "(" + ", ".join(arglists) + ")"
    else:
        annotation += " ".join(arglists)

    kind = KINDS.get(type.name, sublime.KIND_AMBIGUOUS)

    return sublime.CompletionItem(
        trigger=trigger,
        completion=candidate,
        kind=kind,
        annotation=annotation,
        details=details,
    )


def get_completions(view, prefix, point):
    # The AC widget won't show up after typing a character that's in word_separators.
    #
    # Removing the forward slash from word_separators is a no go, though. Therefore,
    # we're gonna do this awful hack where we remove the forward slash from
    # word_separators for the duration of the AC interaction.
    word_separators = view.settings().get("word_separators")

    try:
        view.settings().set("word_separators", word_separators.replace("/", ""))

        if view.match_selector(
            point,
            "source.clojure & (meta.symbol - meta.function.parameters) | (constant.other.keyword - punctuation.definition.keyword)",
        ) and (dialect := dialects.for_point(view, point)) and (client := state.get_client(view.window(), dialect)):
            if scope := selectors.expand_by_selector(view, point, "meta.symbol | constant.other.keyword"):
                prefix = view.substr(scope)

            completion_list = sublime.CompletionList()

            client.backchannel.send({
                "op": edn.Keyword("completions"),
                "prefix": prefix,
                "ns": namespace.name(view),
                "dialect": dialect
            }, handler=lambda response: (
                completion_list.set_completions(
                    map(completion_item, response.get(edn.Keyword("completions"), []))
                )
            ))

            return completion_list
    finally:
        view.settings().set("word_separators", word_separators)
