from ...api import edn
from .. import dialects
from sublime import View, Window
from typing import Union


def get_host(view: View) -> Union[str, None]:
    """Given a Tutkain REPL view, return the hostname associated with the
    view."""
    return view.settings().get("tutkain_repl_host")


def get_port(view: View) -> Union[int, None]:
    """Given a Tutkain REPL view, return the port number associated with the
    view."""
    return view.settings().get("tutkain_repl_port")


def get_dialect(view: View) -> Union[edn.Keyword, None]:
    """Given a Tutkain REPL view, return the dialect associated with the REPL
    view."""
    if dialect := view.settings().get("tutkain_repl_view_dialect"):
        return edn.Keyword(dialect)


def active_repl_view(window: Window) -> Union[View, None]:
    for group in range(window.num_groups() + 1):
        if view := window.active_view_in_group(group):
            if view.settings().get("tutkain_repl_view_dialect"):
                return view


def configure(view, dialect, client):
    window = view.window()
    num_groups = window.num_groups()
    target_group = num_groups - 1

    for group_num in range(0, num_groups):
        if group_num > 0 and not window.views_in_group(group_num):
            target_group = group_num
            break

    view_count = len(window.views_in_group(target_group))

    view.set_name(f"REPL · {dialects.name(dialect)} · {client.host}:{client.port}")
    view.settings().set("line_numbers", False)
    view.settings().set("gutter", False)
    view.settings().set("is_widget", True)
    view.settings().set("scroll_past_end", False)
    view.settings().set("show_definitions", False)
    view.settings().set("translate_tabs_to_spaces", False)
    view.settings().set("auto_indent", False)
    view.settings().set("smart_indent", False)
    view.settings().set("spell_check", False)
    view.settings().set("indent_subsequent_lines", False)
    view.settings().set("detect_indentation", False)
    view.settings().set("auto_complete", False)
    view.settings().set("tutkain_repl_view_dialect", dialect.name or "clj")
    view.settings().set("tutkain_repl_host", client.host)
    view.settings().set("tutkain_repl_port", client.port)
    view.settings().set("scroll_past_end", 0.5)
    view.settings().set("result_file_regex", r"""\s*\[.+?\"(.+?)" (\d+)\]""")
    view.set_read_only(True)
    view.set_scratch(True)
    view.assign_syntax("REPL (Tutkain).sublime-syntax")
    window.set_view_index(view, target_group, view_count)

    return view
