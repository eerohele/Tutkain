import re
import sublime
from . import sexp


def open_round(view, edit):
    ends = []
    selections = view.sel()

    for region in selections:
        begin = region.begin()
        end = region.end() + 1
        view.insert(edit, begin, '(')

        if not sexp.inside_string(view, begin):
            view.insert(edit, end, ')')
            new_end = end + 1
            ends.append(end)

            # For some reason, we have to explicitly account for the NUL
            # character.
            if re.match(r'[^\s\x00]', view.substr(new_end)):
                view.insert(edit, new_end, ' ')

    if ends:
        selections.clear()
        for end in ends:
            selections.add(sublime.Region(end, end))
