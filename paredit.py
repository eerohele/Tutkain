import re
import sublime
from . import sexp


def each_region(view):
    new_selections = []
    selections = view.sel()

    for region in selections:
        yield region, new_selections

    if new_selections:
        selections.clear()
        for region in new_selections:
            selections.add(region)


def open_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in each_region(view):
        begin = region.begin()
        end = region.end() + 1
        view.insert(edit, begin, open_bracket)

        if not sexp.ignore(view, begin):
            view.insert(edit, end, close_bracket)
            new_end = end + 1
            sel.append(sublime.Region(begin + 1, begin + 1))

            # If the character that follows the close bracket we just inserted
            # is a whitespace character, the NUL character, or a close bracket,
            # don't insert a whitespace. Otherwise, do.
            if re.match(r'[^\s\x00\)\]\}]', view.substr(new_end)):
                view.insert(edit, new_end, ' ')


def close_bracket(view, edit, close_bracket):
    for region, sel in each_region(view):
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
        sel.append(sublime.Region(begin + 1, end + 1))


def double_quote(view, edit):
    for region, sel in each_region(view):
        begin = region.begin()
        end = region.end()

        if view.substr(end) == '"':
            sel.append(sublime.Region(end + 1, end + 1))
        elif sexp.inside_string(view, begin):
            view.insert(edit, begin, '\\"')
        elif sexp.inside_comment(view, begin):
            view.insert(edit, begin, '"')
        else:
            view.insert(edit, begin, '""')
            sel.append(sublime.Region(end + 1, end + 1))
