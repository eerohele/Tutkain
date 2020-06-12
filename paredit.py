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


def move(view, forward):
    for region, sel in iterate(view):
        point = region.begin()

        element = find_next_element(view, point) if forward else find_previous_element(view, point)
        new_point = None

        if element:
            new_point = element.end() if forward else element.begin()
        else:
            innermost = sexp.innermost(view, point, edge=False)

            if innermost:
                new_point = innermost.close.end() if forward else innermost.open.begin()

        if new_point is not None:
            sel.append(new_point)
            view.show(new_point)


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

            close_bracket_end = view.find_by_class(
                begin,
                True,
                sublime.CLASS_PUNCTUATION_END
            )

            sel.append(sublime.Region(close_bracket_end, close_bracket_end))


def double_quote(view, edit):
    for region, sel in iterate(view):
        if region.empty():
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
        else:
            this = sexp.innermost(view, region.begin(), edge=False)
            that = sexp.innermost(view, region.end(), edge=False)

            if this == that:
                view.insert(edit, region.end(), '"')
                view.insert(edit, region.begin(), '"')
            else:
                # If the two ends of the region are inside different sexps, abort and insert double
                # quotes at the beginning of the region.
                view.insert(edit, region.begin(), '""')
                sel.append(region.begin() + 1)


def has_null_character(view, point):
    return view.substr(point) == '\x00'


def extract_scope(view, point):
    '''Like View.extract_scope(), but less fussy.

    For example, take this Clojure keyword:

        :foo

    At point 0, the scope name is:

        'source.clojure constant.other.keyword.clojure punctuation.definition.keyword.clojure '

    At point 1, the scope name is:

        'source.clojure constant.other.keyword.clojure '

    View.extract_scope() considers them different scopes, even though the second part of the scope
    name (constant.other.keyword.clojure) is the same.

    This function considers two adjacent points as having the same scope if the second part of the
    scope name is the same.
    '''
    if sexp.ignore(view, point):
        return None

    scope_name = view.scope_name(point)
    scopes = scope_name.split()

    try:
        selector = scopes[1]
    except IndexError:
        # If this point has a single scope name (in practice, 'source.clojure'), there's no way we
        # can know the extent of the syntax scope of this point, so we bail out.
        return None

    max_size = view.size()
    begin = end = point

    while begin >= 1:
        if has_null_character(view, begin) or (
            not view.match_selector(begin - 1, selector) and view.match_selector(begin, selector)
        ):
            break
        else:
            begin -= 1

    while end <= max_size:
        if has_null_character(view, end) or (
            view.match_selector(end - 1, selector) and not view.match_selector(end, selector)
        ):
            break
        else:
            end += 1

    return sublime.Region(begin, end)


def is_insignificant(view, point):
    return re.match(r'[\s,]', view.substr(point))


def is_symbol_character(view, point):
    return re.match(r'[\w\*\+\!\-\_\'\?\<\>\=\/]', view.substr(point))


# FIXME: Remove duplication between this and extract_scope.
def extract_symbol(view, point):
    begin = end = point
    max_size = view.size()

    while begin >= 0:
        if has_null_character(view, begin - 1) or (
            not is_symbol_character(view, begin - 1) and is_symbol_character(view, begin)
        ):
            break
        else:
            begin -= 1

    while end <= max_size:
        if has_null_character(view, end) or (
            is_symbol_character(view, end - 1) and not is_symbol_character(view, end)
        ):
            break
        else:
            end += 1

    return sublime.Region(begin, end)


# TODO: The conditional logic here is a bit convoluted. Can we make it more straightforward?
def find_next_element(view, point):
    max_size = view.size()

    while point < max_size:
        if sexp.has_end_double_quote(view, point) or (
            not sexp.ignore(view, point) and view.substr(point) in sexp.CLOSE
        ):
            return None
        elif is_insignificant(view, point):
            point += 1
        elif sexp.is_next_to_open(view, point):
            return sexp.innermost(view, point).extent()
        else:
            scope = extract_scope(view, point)

            if scope:
                return scope
            elif is_symbol_character(view, point):
                return extract_symbol(view, point)
            else:
                return None


def find_previous_element(view, point):
    while point >= 0:
        if sexp.has_begin_double_quote(view, point - 1) or (
            not sexp.ignore(view, point) and view.substr(point - 1) in sexp.OPEN
        ):
            return None
        elif is_insignificant(view, point - 1):
            point -= 1
        elif view.substr(point - 1) in sexp.CLOSE or view.substr(point - 1) == '"':
            return sexp.innermost(view, point).extent()
        else:
            scope = extract_scope(view, point - 1)

            if scope:
                return scope
            elif is_symbol_character(view, point - 1):
                return extract_symbol(view, point)
            else:
                return None


def forward_slurp(view, edit):
    for region, sel in iterate(view):
        element = None

        # TODO: It would be faster just to find close brackets instead of the entire sexp.
        for s in sexp.walk_outward(view, region.begin()):
            element = find_next_element(view, s.close.end())
            if element:
                break

        if element:
            close_begin = view.find_by_class(
                element.begin(),
                False,
                sublime.CLASS_PUNCTUATION_END
            ) - 1

            close_end = close_begin + 1

            # Save cursor position so we can restore it after slurping.
            sel.append(region)
            # Save close char.
            char = view.substr(close_begin)
            # Put a copy of the close char we found after the element.
            view.insert(edit, element.end(), char)
            # Erase the close char we copied.
            view.erase(edit, sublime.Region(close_begin, close_end))
            # # If we slurped a sexp, indent it.
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def forward_barf(view, edit):
    for region, sel in iterate(view):
        sel.append(region)

        innermost = None
        element = None

        # TODO: It would be faster just to find close brackets instead of the entire sexp.
        for s in sexp.walk_outward(view, region.begin()):
            element = find_previous_element(view, s.close.begin())
            if element:
                innermost = s
                break

        if innermost and element:
            point = innermost.close.begin()
            char = view.substr(point)
            view.erase(edit, sublime.Region(point, point + 1))
            insert_point = max(element.begin() - 1, innermost.open.end())
            view.insert(edit, insert_point, char)

            # If we inserted the close char next to the open char, add a
            # space after the new close char.
            if insert_point - 1 == innermost.open.begin():
                view.insert(edit, insert_point + 1, ' ')

            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def adjacent_element_direction(view, point):
    if not sexp.ignore(view, point) and re.match(r'[^\s,\)\]\}\x00]', view.substr(point)):
        return 1
    elif not sexp.ignore(view, point - 1) and re.match(r'[^\s,\(\[\{\x00]', view.substr(point - 1)):
        return -1
    else:
        return 0


def wrap_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
        point = region.begin()
        direction = adjacent_element_direction(view, point)

        if direction == 1:
            element = find_next_element(view, point)
        elif direction == -1:
            element = find_previous_element(view, point)
        else:
            element = sublime.Region(point, point)
            sel.append(sublime.Region(point + 1, point + 1))

        view.insert(edit, element.end(), close_bracket)
        view.insert(edit, element.begin(), open_bracket)


def forward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin()
            innermost = sexp.innermost(view, point, edge=True)

            if view.match_selector(point, 'constant.character.escape'):
                view.erase(edit, sublime.Region(point, point + 2))
            elif not innermost:
                view.erase(edit, sublime.Region(point, point + 1))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif point == innermost.open.begin() or point == innermost.close.begin():
                sel.append(point + 1)
            else:
                view.erase(edit, sublime.Region(point, point + 1))


def backward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin()
            innermost = sexp.innermost(view, point, edge=True)

            if view.match_selector(point - 1, 'constant.character.escape'):
                view.erase(edit, sublime.Region(point - 2, point))
            elif not innermost:
                view.erase(edit, sublime.Region(point - 1, point))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif (point == innermost.open.end() or point == innermost.close.end() or
                  (not sexp.ignore(view, point) and view.substr(point - 1) in sexp.CLOSE)):
                sel.append(point - 1)
            else:
                view.erase(edit, sublime.Region(point - 1, point))


def raise_sexp(view, edit):
    for region, sel in iterate(view):
        point = region.begin()

        if not sexp.ignore(view, point):
            innermost = sexp.innermost(view, point, edge=False)
            element = find_next_element(view, point)
            view.replace(edit, innermost.extent(), view.substr(element))
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def splice_sexp(view, edit):
    for region, _ in iterate(view):
        point = region.begin()

        innermost = sexp.innermost(view, point, edge=False)

        # Erase the close character
        view.erase(edit, innermost.close)
        # Erase one or more open characters
        view.erase(edit, innermost.open)
        view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def comment_dwim(view, edit):
    for region, sel in iterate(view):
        line = view.line(region.begin())
        n = view.insert(edit, line.end(), ' ; ')
        sel.append(line.end() + n)


def kill(view, edit):
    for region, _ in iterate(view):
        # What should kill do with a non-empty selection?
        point = region.begin()

        innermost = sexp.innermost(view, point, edge=True)

        # Cursive only deletes until newline, we delete the contents of the sexp regardless of
        # newlines. Not sure which is right, but this is easier to implement and makes more sense
        # to me.
        if point == innermost.open.begin() or point == innermost.close.end():
            view.erase(edit, innermost.extent())
        elif point == innermost.open.end() or point == innermost.close.begin():
            view.erase(edit, sublime.Region(innermost.open.end(), innermost.close.begin()))


def semicolon(view, edit):
    for region, sel in iterate(view):
        point = region.begin()

        if sexp.ignore(view, point):
            view.insert(edit, point, ';')
        else:
            innermost = sexp.innermost(view, point, edge=False)

            if innermost:
                view.insert(edit, innermost.close.begin(), '\n')

            element = find_next_element(view, point)

            if element:
                n = view.insert(edit, point, '; ')
            else:
                n = view.insert(edit, point, ' ; ')

            sel.append(point + n)
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def splice_sexp_killing_forward(view, edit):
    for region, _ in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            view.erase(edit, region.cover(innermost.close))
            view.erase(edit, innermost.open)
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def splice_sexp_killing_backward(view, edit, forward=True):
    for region, _ in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            view.erase(edit, innermost.close)
            view.erase(edit, region.cover(innermost.open))
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})


def backward_kill_word(view, edit):
    for region, sel in iterate(view):
        point = view.find_by_class(region.begin(), False, sublime.CLASS_WORD_START)
        sel.append(sublime.Region(point, point))
        char = view.substr(point)

        if char not in sexp.OPEN and char not in sexp.CLOSE:
            view.erase(edit, extract_symbol(view, point))
            view.run_command('tutkain_indent_region', {'scope': 'innermost', 'prune': True})
