from ..log import log
from .. import state
from .. import settings
from .. import inline
from . import views
import sublime

from .keywords import (
    CLIPBOARD,
    ERR,
    IN,
    INLINE,
    OUTPUT,
    RET,
    POINT,
    STRING,
    TAG,
    TAP,
    VAL,
    VIEW_ID,
)


def show_repl_panel(view):
    if (
        view
        and view.element() == "output:output"
        and settings.load().get("auto_show_output_panel", True)
    ):
        views.show_output_panel(sublime.active_window())


def append_to_view(view, characters):
    show_repl_panel(view)

    if view and characters:
        view.set_read_only(False)

        if characters is not None:
            view.run_command(
                "append", {"characters": characters, "scroll_to_end": True}
            )

        view.set_read_only(True)
        view.run_command("move_to", {"to": "eof"})


def append_to_tap_panel(view, val):
    if settings.load().get("tap_panel", False):
        window = view.window() or sublime.active_window()
        views.show_tap_panel(view)
        panel = window.find_output_panel(views.tap_panel_name(view))
        append_to_view(panel, val)


def print_item(view, item):
    characters = item.get(VAL)

    if item.get(TAG) == TAP:
        append_to_tap_panel(view, characters)
    else:
        append_to_view(view, characters)


TAG_ICONS = {
    IN: "chevron-right",
    ERR: "chevron-left",
    RET: "chevron-left",
    TAP: "double-chevron-left",
}


TAG_SCOPES = {
    ERR: "region.redish",
}


def icon_path(tag):
    if icon_name := TAG_ICONS.get(tag):
        return f"Packages/Tutkain/icons/{icon_name}.png"
    else:
        return ""


def add_gutter_marks(view, client, item):
    tag = item.get(TAG)
    key = f"tutkain_gutter_marks/{tag.name}"
    point = view.size() - len(item.get(VAL))
    region = sublime.Region(point, point)

    if tag in state.MARKER_TAGS and (markers := state.get_gutter_markers(view)):
        markers[tag].append(region)

        if tag_markers := markers.get(tag):
            view.add_regions(
                key,
                tag_markers,
                scope=TAG_SCOPES.get(tag, "source"),
                icon=icon_path(tag),
                # TODO: sublime.PERSISTENT?
                flags=sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE,
            )


def print_loop(view, client, options={"gutter_marks": True}):
    try:
        log.debug({"event": "thread/start"})

        while item := client.printq.get():
            if item.get(OUTPUT) == CLIPBOARD:
                sublime.set_clipboard(item.get(STRING))
                sublime.active_window().status_message(
                    "[Tutkain] Evaluation result copied to clipboard."
                )
            elif item.get(OUTPUT) == INLINE:
                window = view.window() or sublime.active_window()

                if target_view := views.find_by_id(window, item.get(VIEW_ID)):
                    inline.clear(target_view)
                    inline.show(target_view, item.get(POINT), item.get(VAL))

            print_item(view, item)

            if options.get("gutter_marks", True):
                add_gutter_marks(view, client, item)

    finally:
        log.debug({"event": "thread/exit"})
