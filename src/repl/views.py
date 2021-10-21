from ...api import edn
from .. import dialects
from sublime import View, Window
from typing import Union

REPL_VIEW_DEFAULT_SETTINGS = {
    "is_widget": True,
    "show_definitions": False,
    "translate_tabs_to_spaces": False,
    "auto_indent": False,
    "smart_indent": False,
    "spell_check": False,
    "indent_subsequent_lines": False,
    "detect_indentation": False,
    "auto_complete": False,
    "scroll_past_end": 0.5,
    "highlight_line": False,
    "line_numbers": False,
    "gutter": False,
}


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
        if (view := window.active_view_in_group(group)) and get_dialect(view):
            return view


def configure(view, dialect, client_id, host, port, settings={}):
    window = view.window()
    num_groups = window.num_groups()
    target_group = num_groups - 1

    for group_num in range(0, num_groups):
        if group_num > 0 and not window.views_in_group(group_num):
            target_group = group_num
            break

    view_count = len(window.views_in_group(target_group))

    # User is not allowed to change these settings:
    internal_settings = {
        "tutkain_repl_client_id",
        "tutkain_repl_view_dialect",
        "tutkain_repl_host",
        "tutkain_repl_port",
    }

    # Default Tutkain REPL view settings merged with user overwrites:
    settings_ = {**REPL_VIEW_DEFAULT_SETTINGS, **settings}

    for settings_name, settings_value in settings_.items():
        if settings_name not in internal_settings:
            view.settings().set(settings_name, settings_value)

    view.set_name(f"REPL · {dialects.name(dialect)} · {host}:{port}")
    view.settings().set("tutkain_repl_client_id", client_id)
    view.settings().set("tutkain_repl_view_dialect", dialect.name or "clj")
    view.settings().set("tutkain_repl_host", host)
    view.settings().set("tutkain_repl_port", port)
    view.set_read_only(True)
    view.set_scratch(True)
    view.assign_syntax("REPL (Tutkain).sublime-syntax")
    window.set_view_index(view, target_group, view_count)

    return view
