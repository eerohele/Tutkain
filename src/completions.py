import sublime

from ..api import edn
from .log import log
from . import base64, dialects, forms, namespace, selectors, sexp, state

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
    "protocol": sublime.KIND_TYPE,
    "navigation": sublime.KIND_NAVIGATION,
    "local": (sublime.KIND_ID_VARIABLE, "l", "Local"),
}


COMPLETION_FORMATS = {
    "text": sublime.CompletionFormat.TEXT,
    "snippet": sublime.CompletionFormat.SNIPPET,
    "command": sublime.CompletionFormat.COMMAND,
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

    type = item.get(edn.Keyword("type"))
    trigger = item.get(edn.Keyword("trigger"))
    completion = item.get(edn.Keyword("completion"), trigger)
    trigger = trigger + " "

    if type == edn.Keyword("navigation"):
        completion = completion + "/"

    arglists = item.get(edn.Keyword("arglists"), [])
    annotation = ""

    if type in {edn.Keyword("method"), edn.Keyword("static-method")}:
        annotation = "(" + ", ".join(arglists) + ")"
    else:
        annotation += " ".join(arglists)

    kind = KINDS.get(type.name, sublime.KIND_AMBIGUOUS)

    completion_format = item.get(
        edn.Keyword("completion-format"), edn.Keyword("text")
    ).name

    completion_format = COMPLETION_FORMATS.get(
        completion_format, sublime.CompletionFormat.TEXT
    )

    item = sublime.CompletionItem(
        trigger=trigger,
        completion=completion,
        completion_format=completion_format,
        kind=kind,
        annotation=annotation,
        details=details,
    )

    return item


def enclosing_sexp_sans_prefix(view, expr, prefix):
    """Given a view, an S-expression, and a prefix, return the S-expression
    with the prefix removed.

    The prefix is unlikely to resolve, so we must remove it from the
    S-expression to be able to analyze it on the server.
    """

    # If the character preceding the prefix is a quote, strip it, because e.g.
    # (require ') is a syntax error.
    if view.match_selector(prefix.begin() - 1, "meta.quote.clojure"):
        begin = prefix.begin() - 1
    else:
        begin = prefix.begin()

    before = sublime.Region(expr.open.region.begin(), begin)
    after = sublime.Region(prefix.end(), expr.close.region.end())
    return view.substr(before) + view.substr(after)


def handler(completion_list, response, flags):
    tag = response.get(edn.Keyword("tag"))

    if tag is not None and tag == edn.Keyword("err"):
        ex = response.get(edn.Keyword("val"))
        log.debug({"event": "error", "exception": ex})
    else:
        completions = response.get(edn.Keyword("completions"), [])
        completion_list.set_completions(map(completion_item, completions), flags=flags)


def intuit_outermost(view, point):
    if view.match_selector(point, "meta.comment.clojure"):
        return sexp.outermost(view, point, ignore={"comment"})
    else:
        return sexp.crude_outermost(view, point)


def get_completions(view, prefix, point):
    preceding_point = point - 1

    # The AC widget won't show up after typing a character that's in word_separators.
    #
    # Removing the forward slash from word_separators is a no go, though. Therefore,
    # we're gonna do this awful hack where we remove the forward slash from
    # word_separators for the duration of the AC interaction.
    word_separators = view.settings().get("word_separators")

    try:
        view.settings().set("word_separators", word_separators.replace("/", ""))

        if (
            view.match_selector(
                preceding_point,
                "source.clojure & (meta.symbol - meta.function.parameters - entity.name) | constant.other.keyword | keyword.operator.macro",
            )
            and (dialect := dialects.for_point(view, preceding_point))
            and (client := state.get_client(view.window(), dialect))
        ):
            if scope := selectors.expand_by_selector(
                view, preceding_point, "meta.symbol | constant.other.keyword"
            ):
                prefix = view.substr(scope)

            completion_list = sublime.CompletionList()

            op = {
                "op": edn.Keyword("completions"),
                "prefix": prefix,
                "ns": namespace.name(view),
                "dialect": dialect,
            }

            if (outermost := intuit_outermost(view, point)) and (
                "analyzer.clj" in client.capabilities
            ):
                code = enclosing_sexp_sans_prefix(view, outermost, scope)
                start_line, start_column = view.rowcol(outermost.open.region.begin())
                line, column = view.rowcol(point)
                op["file"] = view.file_name() or "NO_SOURCE_FILE"
                op["start-line"] = start_line + 1
                op["start-column"] = start_column + 1
                op["line"] = line + 1
                # Since we're removing the prefix from enclosing-sexp, we must
                # subtract its length from the column, too.
                op["column"] = column + 1 - len(prefix)
                op["enclosing-sexp"] = base64.encode(code.encode("utf-8"))

                flags = (
                    sublime.AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS
                    | sublime.AutoCompleteFlags.INHIBIT_REORDER
                )
            else:
                flags = sublime.AutoCompleteFlags.NONE

            client.send_op(
                op, handler=lambda response: handler(completion_list, response, flags)
            )

            return completion_list
    finally:
        view.settings().set("word_separators", word_separators)
