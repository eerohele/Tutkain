import re
import sublime

from . import sexp
from . import indent


def iterate(view):
    '''
    Iterate over each region in all selections.

    After iteration, add all selections saved by consumers.
    '''
    new_regions = []
    selections = view.sel()

    for region in selections:
        yield region, new_regions

    if new_regions:
        selections.clear()
        for region in new_regions:
            selections.add(region)


def open_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
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
    for region, sel in iterate(view):
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
    for region, sel in iterate(view):
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


def find_element(view, point, forward=True):
    start = view.find_by_class(
        point,
        forward,
        sublime.CLASS_PUNCTUATION_START | sublime.CLASS_WORD_START
    )

    flags = view.classify(start)

    if flags & sublime.CLASS_PUNCTUATION_START:
        return sexp.innermost(view, start, absorb=True)
    elif flags & sublime.CLASS_WORD_START:
        return view.word(start)


def forward_slurp(view, edit):
    for region, sel in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False, absorb=True)

        # If we don't find a close char, do nothing.
        if innermost:
            point = innermost.end() - 1
            element = find_element(view, point)

            if element:
                # Save cursor position so we can restore it after slurping.
                sel.append(region)
                # Save close char.
                char = view.substr(point)
                # Put a copy of the close char we found after the element.
                view.insert(edit, element.end(), char)
                # Erase the close char we copied.
                view.erase(edit, sublime.Region(point, point + 1))
                # If we slurped a sexp, indent it.
                indent.indent_region(view, edit, innermost, prune=True)


def forward_barf(view, edit):
    for region, sel in iterate(view):
        sel.append(region)

        innermost = sexp.innermost(view, region.begin(), edge=False, absorb=True)

        if innermost:
            point = innermost.end() - 1
            element = find_element(view, point, forward=False)

            if element:
                char = view.substr(point)
                view.erase(edit, sublime.Region(point, point + 1))
                insert_point = max(element.begin() - 1, innermost.begin() + 1)
                view.insert(edit, insert_point, char)

                # If we inserted the close char next to the open char, add a
                # space after the new close char.
                if insert_point - 1 == innermost.begin():
                    view.insert(edit, insert_point + 1, ' ')

                indent.indent_region(view, edit, innermost, prune=True)
