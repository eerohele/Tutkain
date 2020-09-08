import sublime


def show(view, point, value):
    style = "color: color(var(--foreground) alpha(0.5));"
    html = """<span><span style="{}">=></span> {}</span>""".format(style, value)
    region = sublime.Region(point, point)
    view.add_phantom("tutkain/eval", region, html, sublime.LAYOUT_INLINE)


def clear(view):
    view.erase_phantoms("tutkain/eval")
