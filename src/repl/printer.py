from ..log import log
from .. import settings
from .. import inline
from ...api import edn
from . import views
import sublime


def print_characters(view, characters):
    if characters is not None:
        view.run_command("append", {"characters": characters, "scroll_to_end": True})


def append_to_view(view, characters):
    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command("move_to", {"to": "eof"})


def append_to_tap_panel(view, val):
    if settings.load().get("tap_panel", False):
        window = view.window() or sublime.active_window()

        if view.element() is None:
            output = "view"
        else:
            output = "panel"

        views.show_tap_panel(window, output)
        panel = window.find_output_panel(views.tap_panel_name(output))
        append_to_view(panel, val)


def show_repl_panel(view):
    if view.element() == "output:output":
        views.show_output_panel(sublime.active_window())


def print_loop(view, client):
    try:
        log.debug({"event": "thread/start"})

        while item := client.printq.get():
            if not isinstance(item, dict):
                show_repl_panel(view)
                append_to_view(view, item)
            else:
                tag = item.get(edn.Keyword("tag"))
                val = item.get(edn.Keyword("val"))

                if tag == edn.Keyword("tap"):
                    append_to_tap_panel(view, val)
                else:
                    output = item.get(edn.Keyword("output"), edn.Keyword("view"))

                    if output == edn.Keyword("clipboard"):
                        string = val[:-1] if val[-1] == "\n" else val
                        sublime.set_clipboard(string)
                        sublime.active_window().status_message("[Tutkain] Evaluation result copied to clipboard.")
                    elif output == edn.Keyword("inline"):
                        view_id = item.get(edn.Keyword("view-id"))
                        window = view.window() or sublime.active_window()

                        if target_view := views.find_by_id(window, view_id):
                            inline.clear(target_view)
                            inline.show(target_view, item.get(edn.Keyword("point")), val)
                    else:
                        show_repl_panel(view)

                        # Print invisible Unicode characters (U+2063) around stdout and
                        # stderr to prevent them from getting syntax highlighting.
                        #
                        # This is probably somewhat evil, but the performance is *so*
                        # much better than with view.add_regions.
                        if tag == edn.Keyword("err"):
                            append_to_view(view, '⁣⁣' + val + '⁣⁣')
                        elif tag == edn.Keyword("out"):
                            append_to_view(view, '⁣' + val + '⁣')
                        elif edn.Keyword("debug") in item:
                            log.debug({"event": "info", "item": item.get(edn.Keyword("val"))})
                        elif val := item.get(edn.Keyword("val")):
                            append_to_view(view, val)
    finally:
        log.debug({"event": "thread/exit"})
