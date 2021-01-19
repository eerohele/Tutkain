import itertools

from sublime import Region, DRAW_NO_OUTLINE
from ..log import log


def print_characters(view, characters):
    if characters is not None:
        view.run_command("append", {"characters": characters, "scroll_to_end": True})


def append_to_view(view, characters):
    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command("move_to", {"to": "eof"})


def print_loop(view, printq):
    try:
        log.debug({"event": "thread/start"})
        counter = itertools.count()

        while item := printq.get():
            printable = item.get("printable")
            response = item.get("response")

            append_to_view(view, printable)

            if response and {"out", "err"} & response.keys():
                size = view.size()

                scope = (
                    "tutkain.repl.stderr"
                    if "err" in response
                    else "tutkain.repl.stdout"
                )

                regions = [Region(size - len(printable), size)]

                view.add_regions(
                    str(next(counter)), regions, scope=scope, flags=DRAW_NO_OUTLINE
                )

    finally:
        log.debug({"event": "thread/exit"})
