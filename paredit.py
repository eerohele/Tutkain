import re
import sublime

from . import sexp


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

        if sexp.ignore(view, begin):
            view.insert(edit, begin, close_bracket)
        else:
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


def find_element(view, point, forward=True, stop_at_close=False):
    max_size = view.size()

    while point >= 0 and point <= max_size:
        if forward:
            char = view.substr(point)
        else:
            char = view.substr(point - 1)

        if forward and stop_at_close and char in sexp.CLOSE:
            return None
        elif ((forward and char in sexp.OPEN) or
              (not forward and char in sexp.CLOSE) or
              (not sexp.inside_string(view, point) and char == '"')):
            return sexp.innermost(view, point, absorb=True)
        elif re.match(r'\w', char):
            return view.word(point)
        else:
            if forward:
                point += 1
            else:
                point -= 1


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
                view.run_command('tutkain_indent_region', {'prune': True})


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

                view.run_command('tutkain_indent_region', {'prune': True})


def wrap_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
        previous_char = view.substr(region.begin() - 1)

        # If we're next to a close char, wrap the preceding element. Otherwise, wrap the following
        # element.
        if re.match(r'[\w\"\]\)\}]', previous_char):
            forward = False
        else:
            forward = True

        element = find_element(view, region.begin(), forward=forward, stop_at_close=True)

        if element:
            view.insert(edit, element.end(), close_bracket)
            view.insert(edit, element.begin(), open_bracket)
        else:
            # If we didn't find an element, add an empty pair of brackets.
            view.insert(edit, region.begin(), open_bracket + close_bracket)
            # Move cursors inside the newly added pair.
            sel.append(sublime.Region(region.begin() + 1, region.begin() + 1))


def backward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin() - 1
            next_char = view.substr(region.begin())
            previous_char = view.substr(point)

            # If the previous character is a close bracket or the double quote of a non-empty
            # string, move the cursor one point to the left.
            if ((not sexp.ignore(view, point) and previous_char in sexp.CLOSE)
               or (previous_char == '"' and next_char != '"')):
                sel.append(point)
            # If the previous character is an open bracket of an empty sexp or the double quote of
            # an empty string, delete the empty string or sexp.
            elif ((not sexp.ignore(view, point) and previous_char in sexp.OPEN)
                  or (previous_char == '"' and next_char == '"')):
                innermost = sexp.innermost(view, point, absorb=True)
                if innermost.size() == 2:
                    view.erase(edit, innermost)
            # Otherwise, delete the previous character.
            else:
                view.erase(edit, sublime.Region(point, point + 1))


def raise_sexp(view, edit):
    for region, _ in iterate(view):
        point = region.begin()

        if not sexp.ignore(view, point):
            innermost = sexp.innermost(view, point, absorb=False, edge=False)
            element = find_element(view, point, stop_at_close=True)
            view.replace(edit, innermost, view.substr(element))
            view.run_command('tutkain_indent_region')
