from ..log import log
from .. import settings
from .. import inline
from . import views
import sublime


def print_characters(view, characters):
    if characters is not None:
        view.run_command("append", {"characters": characters, "scroll_to_end": True})


def show_repl_panel(view):
    if view and view.element() == "output:output" and settings.load().get("auto_show_output_panel", True):
        views.show_output_panel(sublime.active_window())


def append_to_view(view, characters):
    show_repl_panel(view)

    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command("move_to", {"to": "eof"})


def append_to_tap_panel(view, val):
    if settings.load().get("tap_panel", False):
        window = view.window() or sublime.active_window()
        views.show_tap_panel(view)
        panel = window.find_output_panel(views.tap_panel_name(view))
        append_to_view(panel, val)


def print_loop(view, q):
    try:
        log.debug({"event": "thread/start"})

        while item := q.get():
            if item["target"] == "input":
                append_to_view(view, item["val"])
                l = len(item["val"])
                indicators = view.settings().get("tutkain_repl_indicators", [])
                indicators.append(sublime.Region(view.size() - l, view.size() - l).to_tuple())
                view.settings().set("tutkain_repl_indicators", indicators)

                view.add_regions(
                    "tutkain_repl_indicators",
                    list(map(lambda x: sublime.Region(x[0], x[1]), view.settings().get("tutkain_repl_indicators"))),
                    scope="source",
                    icon="Packages/Tutkain/chevron-right.png", flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
                )
            elif item["target"] == "tap":
                append_to_tap_panel(view, item["val"])
                l = len(item["val"])
                indicators = view.settings().get("tutkain_tap_indicators", [])
                indicators.append(sublime.Region(view.size() - l, view.size() - l).to_tuple())
                view.settings().set("tutkain_tap_indicators", indicators)

                view.add_regions(
                    "tutkain_tap_indicators",
                    list(map(lambda x: sublime.Region(x[0], x[1]), view.settings().get("tutkain_tap_indicators"))),
                    scope="source",
                    icon="Packages/Tutkain/tap.png", flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
                )
            elif item["target"] == "view":
                append_to_view(view, item["val"])
                l = len(item["val"])

                if item.get("tag") == "err":
                    indicators = view.settings().get("tutkain_repl_indicators_err", []) or []
                    indicators.append(sublime.Region(view.size() - l, view.size() - l).to_tuple())
                    view.settings().set("tutkain_repl_indicators_err", indicators)
                    scope = "region.redish"

                    icon = "Packages/Tutkain/chevron-left.png"
                    view.add_regions(
                        "tutkain_repl_indicators_err",
                        list(map(lambda x: sublime.Region(x[0], x[1]), view.settings().get("tutkain_repl_indicators_err"))),
                        scope=scope,
                        icon=icon, flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
                    )
                elif item.get("tag") == "out":
                    pass
                    # indicators = view.settings().get("tutkain_repl_indicators_out", [])
                    # indicators.append(sublime.Region(view.size() - l, view.size() - l).to_tuple())
                    # view.settings().set("tutkain_repl_indicators_out", indicators)
                    # scope = "source"
                    # icon = "Packages/Tutkain/circle.png"
                    # view.add_regions(
                    #     "tutkain_repl_indicators_out",
                    #     list(map(lambda x: sublime.Region(x[0], x[1]), view.settings().get("tutkain_repl_indicators_out"))),
                    #     scope=scope,
                    #     icon=icon, flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
                    # )
                else:
                    indicators = view.settings().get("tutkain_repl_indicators_ret", [])
                    indicators.append(sublime.Region(view.size() - l, view.size() - l).to_tuple())
                    view.settings().set("tutkain_repl_indicators_ret", indicators)
                    scope = "source"
                    icon = "Packages/Tutkain/chevron-left.png"
                    view.add_regions(
                        "tutkain_repl_indicators_ret",
                        list(map(lambda x: sublime.Region(x[0], x[1]), view.settings().get("tutkain_repl_indicators_ret"))),
                        scope=scope,
                        icon=icon, flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
                    )

            elif item["target"] == "clipboard":
                sublime.set_clipboard(item["val"])
                sublime.active_window().status_message("[Tutkain] Evaluation result copied to clipboard.")
            elif item["target"] == "inline":
                window = view.window() or sublime.active_window()

                if target_view := views.find_by_id(window, item["view-id"]):
                    inline.clear(target_view)
                    inline.show(target_view, item["point"], item["val"])
    finally:
        log.debug({"event": "thread/exit"})
