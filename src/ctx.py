import sublime

from . import base64


def get(view):
    return view.substr(sublime.Region(0, view.size()))


def encoded(view):  # TODO: Only send context up to point
    return base64.encode(get(view).encode("utf-8"))
