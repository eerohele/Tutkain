import sublime
import re
import html
from inspect import cleandoc

from ..api import edn


keys = []


def show(view, item, inline_result=True):
    region = item.get(edn.Keyword("region"))
    region = sublime.Region(region[0], region[1])
    value = item.get(edn.Keyword("val"))
    value = html.escape(value)

    if item.get(edn.Keyword("tag")) == edn.Keyword("err"):
        annotation_color = view.style_for_scope("region.redish")["foreground"]
        value = f"""<span style="color: var(--redish)">{value}</span>"""
    else:
        annotation_color = view.style_for_scope("region.greenish")["foreground"]

    print(region)

    view.add_regions(
        "tutkain/eval",
        [region],
        scope="region.greenish",
        annotations=[value],
        annotation_color=annotation_color,
        flags=sublime.NO_UNDO | sublime.DRAW_NO_FILL
    )


def clear(view):
    view.erase_regions("tutkain/eval")
