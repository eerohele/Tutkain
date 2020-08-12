import re
from sublime import Region

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

        if forward:
            element = sexp.find_next_element(view, point)
        else:
            element = sexp.find_previous_element(view, point)

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
            sel.append(Region(begin + 1, begin + 1))

            # If the character that follows the close bracket we just inserted
            # is a whitespace character, the NUL character, or a close bracket,
            # don't insert a whitespace. Otherwise, do.
            if re.match(r'[^\s\x00\)\]\}]', view.substr(new_end)):
                view.insert(edit, new_end, ' ')


def close_bracket(view, edit, close_bracket):
    for region, sel in iterate(view):
        point = region.begin()

        if sexp.ignore(view, point):
            view.insert(edit, point, close_bracket)
        else:
            innermost = sexp.innermost(view, point, edge=False)

            # Get the region that starts at the current point and ends before the
            # close bracket and trim the whitespace on its right.
            if innermost:
                replacee = Region(point, innermost.close.begin())
                view.replace(edit, replacee, view.substr(replacee).rstrip())
                sel.append(sexp.innermost(view, point, edge=False).close.end())


def double_quote(view, edit):
    for region, sel in iterate(view):
        if region.empty():
            begin = region.begin()
            end = region.end()

            if view.substr(end) == '"':
                sel.append(Region(end + 1, end + 1))
            elif sexp.inside_string(view, begin):
                view.insert(edit, begin, '\\"')
            elif sexp.inside_comment(view, begin):
                view.insert(edit, begin, '"')
            else:
                view.insert(edit, begin, '""')
                sel.append(Region(end + 1, end + 1))
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


def find_slurp_barf_targets(view, point, finder):
    element = None
    innermost = None

    for s in sexp.walk_outward(view, point):
        element = finder(s)

        if element:
            innermost = s
            break

    return element, innermost


def forward_slurp(view, edit):
    for region, sel in iterate(view):
        element, innermost = find_slurp_barf_targets(
            view,
            region.begin(),
            lambda s: sexp.find_next_element(view, s.close.end())
        )

        if element:
            # Save cursor position so we can restore it after slurping.
            sel.append(region)
            # Save close char.
            char = view.substr(innermost.close)
            # Put a copy of the close char we found after the element.
            view.insert(edit, element.end(), char)
            # Erase the close char we copied.
            view.erase(edit, innermost.close)
            # If we slurped a sexp, indent it.
            indent.indent_region(
                view, edit, sexp.innermost(view, region.begin(), edge=False).extent(), prune=True
            )


def backward_slurp(view, edit):
    for region, sel in iterate(view):
        element, innermost = find_slurp_barf_targets(
            view,
            region.begin(),
            lambda s: sexp.find_previous_element(view, s.open.begin())
        )

        if element:
            sel.append(region)
            chars = view.substr(innermost.open)
            view.erase(edit, innermost.open)
            view.insert(edit, element.begin(), chars)
            view.run_command('tutkain_indent_sexp', {'scope': 'innermost', 'prune': True})


def forward_barf(view, edit):
    for region, sel in iterate(view):
        sel.append(region)

        element, innermost = find_slurp_barf_targets(
            view,
            region.begin(),
            lambda s: sexp.find_previous_element(view, s.close.begin())
        )

        if innermost and element:
            point = innermost.close.begin()
            char = view.substr(point)
            view.erase(edit, Region(point, point + 1))
            insert_point = max(element.begin() - 1, innermost.open.end())
            view.insert(edit, insert_point, char)

            # If we inserted the close char next to the open char, add a
            # space after the new close char.
            if insert_point - 1 == innermost.open.begin():
                view.insert(edit, insert_point + 1, ' ')

            view.run_command('tutkain_indent_sexp', {'scope': 'innermost', 'prune': True})


def backward_barf(view, edit):
    for region, sel in iterate(view):
        sel.append(region)

        element, innermost = find_slurp_barf_targets(
            view,
            region.begin(),
            lambda s: sexp.find_next_element(view, s.open.end())
        )

        if innermost and element:
            insert_point = min(element.end() + 1, innermost.close.begin())
            view.insert(edit, insert_point, view.substr(innermost.open))
            view.erase(edit, innermost.open)

            if insert_point == innermost.close.begin():
                view.insert(edit, insert_point - 1, ' ')

            view.run_command('tutkain_indent_sexp', {'scope': 'innermost', 'prune': True})


def wrap_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
        point = region.begin()
        element = sexp.find_adjacent_element(view, point)

        # cursor is in between the dispatch macro and an open paren
        if (
            element and
            view.match_selector(point - 1, 'keyword.operator.macro') and
            view.match_selector(point, 'punctuation.section.parens.begin')
        ):
            element = Region(element.begin() + 1, element.end())

        if not element:
            element = Region(point, point)
            sel.append(Region(point + 1, point + 1))

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
                view.erase(edit, Region(point, point + 2))
            elif not innermost:
                view.erase(edit, Region(point, point + 1))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif point == innermost.open.end() - 1 or point == innermost.close.begin():
                sel.append(point + 1)
            else:
                view.erase(edit, Region(point, point + 1))


def backward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin()
            innermost = sexp.innermost(view, point, edge=True)

            if view.match_selector(point - 1, 'constant.character.escape'):
                view.erase(edit, Region(point - 2, point))
            elif not innermost:
                view.erase(edit, Region(point - 1, point))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif view.match_selector(point - 1, 'meta.sexp.begin | meta.sexp.end'):
                sel.append(point - 1)
            else:
                view.erase(edit, Region(point - 1, point))


def raise_sexp(view, edit):
    for region, sel in iterate(view):
        point = region.begin()

        if not sexp.ignore(view, point):
            innermost = sexp.innermost(view, point, edge=False)

            if region.empty():
                element = sexp.find_next_element(view, point)
                view.replace(edit, innermost.extent(), view.substr(element))
                view.run_command('tutkain_indent_sexp', {'scope': 'innermost', 'prune': True})
            else:
                view.replace(edit, innermost.extent(), view.substr(region))


def splice_sexp(view, edit):
    for region, _ in iterate(view):
        point = region.begin()

        innermost = sexp.innermost(view, point, edge=False)

        # Erase the close character
        view.erase(edit, innermost.close)
        # Erase one or more open characters
        view.erase(edit, innermost.open)
        view.run_command('tutkain_indent_sexp', {'scope': 'innermost', 'prune': True})


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

        if innermost:
            # Cursive only deletes until newline, we delete the contents of the sexp regardless of
            # newlines. Not sure which is right, but this is easier to implement and makes more
            # sense to me.
            if point == innermost.open.begin() or point == innermost.close.end():
                view.erase(edit, innermost.extent())
            elif point == innermost.open.end() or point == innermost.close.begin():
                view.erase(edit, Region(innermost.open.end(), innermost.close.begin()))


def semicolon(view, edit):
    for region, sel in iterate(view):
        point = region.begin()

        if sexp.ignore(view, point):
            view.insert(edit, point, ';')
        else:
            innermost = sexp.innermost(view, point, edge=False)

            if innermost and view.line(point).contains(innermost.close):
                view.insert(edit, innermost.close.begin(), '\n')

            if not re.match(r'[\s\(\[\{\)\]\}]', view.substr(point - 1)):
                n = view.insert(edit, point, ' ;')
            else:
                n = view.insert(edit, point, ';')

            sel.append(point + n)


def splice_sexp_killing_forward(view, edit):
    for region, _ in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            view.erase(edit, region.cover(innermost.close))
            view.erase(edit, innermost.open)
            view.run_command('tutkain_indent_sexp', {'scope': 'innermost', 'prune': True})


def splice_sexp_killing_backward(view, edit, forward=True):
    for region, _ in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            view.erase(edit, innermost.close)
            view.erase(edit, region.cover(innermost.open))
            view.run_command('tutkain_indent_sexp', {'scope': 'innermost', 'prune': True})


def kill_element(view, edit, forward):
    for region, sel in iterate(view):
        point = region.begin()

        if sexp.ignore(view, point):
            word = view.word(point)

            if word:
                view.erase(edit, word)
        else:
            if forward:
                element = sexp.find_next_element(view, point)
            else:
                element = sexp.find_previous_element(view, point)

            if element:
                if forward:
                    sel.append(point)

                view.erase(edit, element)


def backward_move_element(view, edit):
    for region, sel in iterate(view):
        point = region.begin()
        element = sexp.find_adjacent_element(view, point)

        if element:
            element_str = view.substr(element)
            previous_element = sexp.find_previous_element(view, element.begin())

            if previous_element:
                sel.append(previous_element.begin())

                if view.match_selector(element.begin() - 1, 'punctuation'):
                    erase = element
                else:
                    erase = Region(element.begin() - 1, element.end())

                view.erase(edit, erase)
                view.insert(edit, previous_element.begin(), element_str + ' ')


def forward_move_element(view, edit):
    for region, sel in iterate(view):
        element = sexp.find_adjacent_element(view, region.begin())

        if element:
            element_str = view.substr(element)
            next_element = sexp.find_next_element(view, element.end())

            if next_element:
                if view.match_selector(element.end(), 'punctuation'):
                    erase = element
                else:
                    erase = Region(element.begin(), element.end() + 1)

                view.erase(edit, erase)
                point = next_element.end() - erase.size()
                sel.append(point + 1)
                view.insert(edit, point, ' ' + element_str)
