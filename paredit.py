import re
import sublime
from . import sexp


def open_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]
    begins = []
    selections = view.sel()

    for region in selections:
        begin = region.begin()
        end = region.end() + 1
        view.insert(edit, begin, open_bracket)

        if not sexp.ignore(view, begin):
            view.insert(edit, end, close_bracket)
            new_end = end + 1
            begins.append(begin + 1)

            # If the character that follows the close bracket we just inserted
            # is a whitespace character, the NUL character, or a close bracket,
            # don't insert a whitespace. Otherwise, do.
            if re.match(r'[^\s\x00\)\]\}]', view.substr(new_end)):
                view.insert(edit, new_end, ' ')

    if begins:
        selections.clear()
        for begin in begins:
            selections.add(sublime.Region(begin, begin))
