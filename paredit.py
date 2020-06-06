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


def find_next_bracket_end(view, point):
    end = view.find_by_class(point, True, sublime.CLASS_PUNCTUATION_END)
    return sublime.Region(end - 1, end)


def find_next_slurpable(view, point):
    start = view.find_by_class(
        point,
        True,
        sublime.CLASS_PUNCTUATION_START | sublime.CLASS_WORD_START
    )

    flags = view.classify(start)

    if flags & sublime.CLASS_PUNCTUATION_START:
        return sexp.innermost(view, start, absorb=True)
    elif flags & sublime.CLASS_WORD_START:
        return view.word(start)


def forward_slurp(view, edit):
    for region, sel in iterate(view):
        bracket = find_next_bracket_end(view, region.begin())
        bracket_string = view.substr(bracket)

        # If we don't find a close bracket or a double quote, do nothing.
        if bracket_string == '"' or bracket_string in sexp.CLOSE:
            slurpable = find_next_slurpable(view, bracket.end())

            if slurpable:
                # Save cursor position so we can restore it after slurping.
                sel.append(region)

                # Put a copy of the close bracket we found after the slurpable.
                view.insert(edit, slurpable.end(), view.substr(bracket))
                # Erase the close bracket we copied.
                view.erase(edit, bracket)

                # If we slurped a sexp, indent it.
                if not sexp.ignore(view, slurpable.begin()):
                    innermost = sexp.innermost(
                        view,
                        region.begin(),
                        edge=False,
                        absorb=True
                    )

                    indent.indent_region(view, edit, innermost, prune=True)
