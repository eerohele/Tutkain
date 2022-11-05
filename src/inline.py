import html
import re
from inspect import cleandoc

import sublime


def format(form):
    if lines := cleandoc(form).splitlines():
        first_line = lines[0] + "\n"
        next_lines = "\n".join(map(lambda line: (3 * "&nbsp;") + line, lines[1:]))

        if next_lines:
            next_lines += "\n"

        return f"""{first_line}{next_lines}"""


def show(view, point, value, inline_result=True):
    layout = sublime.LAYOUT_INLINE
    value = html.escape(value)

    if inline_result == "block":
        value = format(
            re.sub(
                r"(?m)^(\s+)", lambda s: "&nbsp;" * (s.span()[1] - s.span()[0]), value
            )
        ).replace("\n", "<br/>")

        layout = sublime.LAYOUT_BLOCK

    style = "color: color(var(--foreground) alpha(0.5));"
    html_text = """<p style="margin: 0"><span style="{}">=></span> {}</p>""".format(
        style, value
    )
    region = sublime.Region(point, point)
    view.add_phantom("tutkain/eval", region, html_text, layout)


def clear(view):
    view.erase_phantoms("tutkain/eval")
