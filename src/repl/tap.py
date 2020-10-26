from ..log import log

from . import printer


panel_name = "tutkain.tap_panel"


def create_panel(window):
    panel = window.find_output_panel(panel_name)

    if panel is None:
        panel = window.create_output_panel(panel_name)
        panel.settings().set("line_numbers", False)
        panel.settings().set("gutter", False)
        panel.settings().set("is_widget", True)
        panel.settings().set("scroll_past_end", False)
        panel.assign_syntax("Clojure (Tutkain).sublime-syntax")

    return panel


def tap_loop(window, tapq):
    try:
        log.debug({'event': 'thread/start'})

        create_panel(window)

        while True:
            tap = tapq.get()

            if tap is None:
                break

            log.debug({"event": "tapq/recv", "data": tap})

            window.run_command("show_panel", {"panel": f"output.{panel_name}"})
            panel = window.find_output_panel(panel_name)
            printer.append_to_view(panel, tap.get("tap"))
    finally:
        log.debug({"event": "thread/exit"})
