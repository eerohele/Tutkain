import re
import sublime
from . import sexp


def open_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]
    regions = []
    selections = view.sel()

    for region in selections:
        begin = region.begin()
        end = region.end() + 1
        view.insert(edit, begin, open_bracket)

        if not sexp.ignore(view, begin):
            view.insert(edit, end, close_bracket)
            new_end = end + 1
            regions.append(sublime.Region(begin + 1, begin + 1))

            # If the character that follows the close bracket we just inserted
            # is a whitespace character, the NUL character, or a close bracket,
            # don't insert a whitespace. Otherwise, do.
            if re.match(r'[^\s\x00\)\]\}]', view.substr(new_end)):
                view.insert(edit, new_end, ' ')

    if regions:
        selections.clear()
        for region in regions:
            selections.add(region)


def close_bracket(view, edit, close_bracket):
    selections = view.sel()
    regions = []

    for region in selections:
        begin = region.begin()
        end = region.end()

        close_bracket_begin = view.find_by_class(
            begin,
            True,
            sublime.CLASS_PUNCTUATION_END
        ) - 1

        # Get the region that starts at the current point and ends before the
        # close bracket and trim the whitespace on its right.
        replacee = sublime.Region(begin, close_bracket_begin)
        view.replace(edit, replacee, view.substr(replacee).rstrip())

        regions.append(sublime.Region(begin + 1, end + 1))

    # Move cursors one point forward.
    if regions:
        selections.clear()
        for region in regions:
            selections.add(region)
