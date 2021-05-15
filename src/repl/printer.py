from ..log import log
from ...api import edn
from . import tap


def print_characters(view, characters):
    if characters is not None:
        view.run_command("append", {"characters": characters, "scroll_to_end": True})


def append_to_view(view, characters):
    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command("move_to", {"to": "eof"})


def print_loop(view, client):
    try:
        log.debug({"event": "thread/start"})

        while item := client.printq.get():
            printable = item.get("printable")
            response = item.get("response")
            tag = response.get(edn.Keyword("tag"))

            if tag == edn.Keyword("tap"):
                view.window().run_command("show_panel", {"panel": f"output.{tap.panel_name}"})
                panel = view.window().find_output_panel(tap.panel_name)
                append_to_view(panel, printable)
            elif tag == edn.Keyword("err"):
                append_to_view(view, '⁣⁣' + printable + '⁣⁣')
            elif tag == edn.Keyword("out"):
                # Print U+2063 around stdout to prevent them from getting syntax highlighting.
                #
                # This is probably somewhat evil, but the performance is *so* much better than
                # with view.add_regions.
                append_to_view(view, '⁣' + printable + '⁣')
            else:
                append_to_view(view, printable)
    finally:
        log.debug({"event": "thread/exit"})
