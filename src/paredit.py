import re
from sublime import Region

from . import forms
from . import indent
from . import selectors
from . import sexp


def iterate(view):
    """
    Iterate over each region in all selections.

    After iteration, add all selections saved by consumers.
    """
    new_regions = []
    selections = view.sel()

    for region in selections:
        yield region, new_regions

    if new_regions:
        selections.clear()
        for region in new_regions:
            selections.add(region)


def move(view, forward, extend):
    for region, sel in iterate(view):
        if forward:
            point = region.end()
            form = forms.find_next(view, point)
        else:
            point = region.begin()
            form = forms.find_previous(view, point)

        new_point = None

        if form:
            new_point = form.end() if forward else form.begin()
        else:
            innermost = sexp.innermost(view, point, edge=False)

            if innermost:
                new_point = innermost.close.end() if forward else innermost.open.begin()

        if new_point is not None:
            if extend and forward:
                sel.append(Region(point, new_point).cover(region))
            elif extend and not forward:
                sel.append(region.cover(Region(new_point, point)))
            else:
                sel.append(new_point)

            view.show(new_point)


def open_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
        begin = region.begin()
        end = region.end() + 1
        view.insert(edit, begin, open_bracket)

        if not selectors.ignore(view, begin):
            view.insert(edit, end, close_bracket)
            new_end = end + 1
            sel.append(Region(begin + 1, begin + 1))

            # If the character that follows the close bracket we just inserted
            # is a whitespace character, the NUL character, or a close bracket,
            # don't insert a whitespace. Otherwise, do.
            if re.match(r"[^\s\x00\)\]\}]", view.substr(new_end)):
                view.insert(edit, new_end, " ")


def close_bracket(view, edit, close_bracket):
    for region, sel in iterate(view):
        point = region.begin()

        if selectors.ignore(view, point):
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
            elif selectors.inside_string(view, begin):
                view.insert(edit, begin, '\\"')
            elif selectors.inside_comment(view, begin):
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
    form = None
    innermost = None

    for s in sexp.walk_outward(view, point, edge=False):
        form = finder(s)

        if form:
            innermost = s
            break

    return form, innermost


def forward_slurp(view, edit):
    for region, sel in iterate(view):
        form, innermost = find_slurp_barf_targets(
            view, region.begin(), lambda s: forms.find_next(view, s.close.end())
        )

        if form:
            # Save cursor position so we can restore it after slurping.
            sel.append(region)
            # Save close char.
            char = view.substr(innermost.close)
            # Put a copy of the close char we found after the form.
            view.insert(edit, form.end(), char)
            # Erase the close char we copied.
            view.erase(edit, innermost.close)
            # If we slurped a sexp, indent it.
            indent.indent_region(
                view,
                edit,
                sexp.innermost(view, region.begin(), edge=False).extent(),
                prune=True,
            )


def backward_slurp(view, edit):
    for region, sel in iterate(view):
        form, innermost = find_slurp_barf_targets(
            view, region.begin(), lambda s: forms.find_previous(view, s.open.begin())
        )

        if form:
            chars = view.substr(innermost.open)
            view.erase(edit, innermost.open)
            view.insert(edit, form.begin(), chars)
            new_innermost = sexp.innermost(view, form.begin(), edge="forward")
            indent.indent_region(view, edit, new_innermost.extent(), prune=True)
            innermost_after_indent = sexp.innermost(view, new_innermost.open.begin(), edge="forward")

            # If pruning changes the size of the sexp we slurped into, move the
            # caret(s) in front the first form in the sexp. If not, keep the
            # carets where they were.
            if new_innermost.extent().size() != innermost_after_indent.extent().size():
                last_form = forms.find_previous(view, innermost_after_indent.close.begin())
                sel.append(last_form.begin())
            else:
                sel.append(region)


def forward_barf(view, edit):
    for region, sel in iterate(view):
        sel.append(region)

        form, innermost = find_slurp_barf_targets(
            view, region.begin(), lambda s: forms.find_previous(view, s.close.begin())
        )

        if innermost and form:
            point = innermost.close.begin()
            char = view.substr(point)

            if previous_form := forms.find_previous(view, form.begin()):
                new_close_pos = previous_form.end()
            else:
                new_close_pos = form.begin() - 1

            view.erase(edit, Region(point, point + 1))
            insert_point = max(new_close_pos, innermost.open.end())
            view.insert(edit, insert_point, char)

            # If we inserted the close char next to the open char, add a
            # space after the new close char.
            if insert_point - 1 == innermost.open.begin():
                view.insert(edit, insert_point + 1, " ")

            # Reindent the form we barfed from
            indent.indent_region(
                view,
                edit,
                sexp.innermost(view, innermost.open.end(), edge=False).extent(),
                prune=True
            )

            # Reindent the form we barfed
            indent.indent_region(
                view,
                edit,
                forms.find_next(view, insert_point + 1),
                prune=True
            )


def backward_barf(view, edit):
    for region, sel in iterate(view):
        sel.append(region)

        form, innermost = find_slurp_barf_targets(
            view, region.begin(), lambda s: forms.find_next(view, s.open.end())
        )

        if innermost and form:
            insert_point = min(form.end() + 1, innermost.close.begin())
            view.insert(edit, insert_point, view.substr(innermost.open))
            view.erase(edit, innermost.open)

            if insert_point == innermost.close.begin():
                view.insert(edit, insert_point - 1, " ")

            view.run_command(
                "tutkain_indent_sexp", {"scope": "innermost", "prune": True}
            )


def wrap_bracket(view, edit, open_bracket):
    close_bracket = sexp.OPEN[open_bracket]

    for region, sel in iterate(view):
        if not region.empty():
            view.insert(edit, region.end(), close_bracket)
            view.insert(edit, region.begin(), open_bracket)
        else:
            point = region.begin()
            form = forms.find_adjacent(view, point)

            # cursor is in between the dispatch macro and an open paren
            if (
                form
                and view.match_selector(point - 1, "keyword.operator.macro")
                and view.match_selector(point, selectors.SEXP_BEGIN)
            ):
                form = Region(form.begin() + 1, form.end())

            if not form:
                form = Region(point, point)
                sel.append(Region(point + 1, point + 1))

            view.insert(edit, form.end(), close_bracket)
            view.insert(edit, form.begin(), open_bracket)


def forward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin()
            innermost = sexp.innermost(view, point, edge="forward")

            if view.match_selector(point, "constant.character"):
                erase = selectors.expand_by_selector(view, point, "constant.character")
                view.erase(edit, erase)
            elif not innermost:
                view.erase(edit, Region(point, point + 1))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif view.match_selector(point, selectors.SEXP_DELIMITERS):
                sel.append(point + 1)
            else:
                view.erase(edit, Region(point, point + 1))


def backward_delete(view, edit):
    for region, sel in iterate(view):
        if not region.empty():
            view.erase(edit, region)
        else:
            point = region.begin()
            innermost = sexp.innermost(view, point, edge="backward")

            if view.match_selector(point - 1, "constant.character"):
                erase = selectors.expand_by_selector(view, point - 1, "constant.character")
                view.erase(edit, erase)
            elif not innermost:
                view.erase(edit, Region(point - 1, point))
            elif innermost.is_empty() and innermost.contains(point):
                view.erase(edit, innermost.extent())
            elif view.match_selector(point - 1, selectors.SEXP_DELIMITERS):
                sel.append(point - 1)
            else:
                view.erase(edit, Region(point - 1, point))


def raise_sexp(view, edit):
    for region, sel in iterate(view):
        point = region.begin()

        if not selectors.ignore(view, point):
            innermost = sexp.innermost(view, point, edge=False)

            if region.empty():
                form = forms.find_next(view, point)
                view.replace(edit, innermost.extent(), view.substr(form))
                view.run_command(
                    "tutkain_indent_sexp", {"scope": "innermost", "prune": True}
                )
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
        view.run_command("tutkain_indent_sexp", {"scope": "innermost", "prune": True})


def comment_dwim(view, edit):
    for region, sel in iterate(view):
        line = view.line(region.begin())
        n = view.insert(edit, line.end(), " ; ")
        sel.append(line.end() + n)


def semicolon(view, edit):
    for region, sel in iterate(view):
        point = region.begin()

        if selectors.ignore(view, point):
            view.insert(edit, point, ";")
        else:
            innermost = sexp.innermost(view, point, edge=False)

            if innermost and view.line(point).contains(innermost.close):
                view.insert(edit, innermost.close.begin(), "\n")

            if not re.match(r"[\s\(\[\{\)\]\}]", view.substr(point - 1)):
                n = view.insert(edit, point, " ;")
            else:
                n = view.insert(edit, point, ";")

            sel.append(point + n)


def splice_sexp_killing_forward(view, edit):
    for region, _ in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            view.erase(edit, region.cover(innermost.close))
            view.erase(edit, innermost.open)
            view.run_command(
                "tutkain_indent_sexp", {"scope": "innermost", "prune": True}
            )


def splice_sexp_killing_backward(view, edit, forward=True):
    for region, _ in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            view.erase(edit, innermost.close)
            view.erase(edit, region.cover(innermost.open))
            view.run_command(
                "tutkain_indent_sexp", {"scope": "innermost", "prune": True}
            )


def kill_form(view, edit, forward):
    for region, sel in iterate(view):
        point = region.begin()

        if not region.empty():
            view.erase(edit, region)
        elif selectors.ignore(view, point):
            word = view.word(point)

            if word:
                view.erase(edit, word)
        else:
            if forward:
                form = forms.find_next(view, point)
            else:
                form = forms.find_previous(view, point)

            if form:
                if forward:
                    sel.append(point)

                view.erase(edit, region.cover(form))


def backward_move_form(view, edit):
    for region, sel in iterate(view):
        form = region

        if region.empty():
            form = forms.find_adjacent(view, region.begin())

        previous_form = forms.find_previous(view, form.begin())

        if previous_form:
            form_str = view.substr(form)
            previous_form_str = view.substr(previous_form)
            between = view.substr(Region(previous_form.end(), form.begin()))
            view.erase(edit, Region(previous_form.begin(), form.end()))
            view.insert(edit, previous_form.begin(), form_str + between + previous_form_str)

            begin = previous_form.begin()

            if region.empty():
                sel.append(begin)
            else:
                sel.append(Region(begin + form.size(), begin))


def forward_move_form(view, edit):
    for region, sel in iterate(view):
        form = region

        if region.empty():
            form = forms.find_adjacent(view, region.begin())

        next_form = forms.find_next(view, form.end())

        if next_form:
            form_str = view.substr(form)
            next_form_str = view.substr(next_form)
            between = view.substr(Region(form.end(), next_form.begin()))
            view.erase(edit, Region(form.begin(), next_form.end()))
            before = next_form_str + between
            view.insert(edit, form.begin(), before + form_str)

            begin = form.begin() + len(before)

            if region.empty():
                sel.append(begin)
            else:
                end = begin + len(form_str)
                sel.append(Region(begin, end))


# FIXME: This is awful. Also, it doesn't handle line breaks.
def thread(view, edit, arrow):
    for region, sel in iterate(view):
        point = region.begin()

        if not selectors.ignore(view, point):
            if region.empty():
                form = forms.find_next(view, point)
            else:
                form = region

            innermost = sexp.innermost(view, point, edge=False)

            def thread_unthreaded():
                characters = "({} {} ".format(arrow, view.substr(form))
                insert = view.insert(edit, innermost.open.begin(), characters)
                begin = insert + form.begin()
                view.insert(edit, innermost.close.end() + insert, ")")

                erase = Region(begin - 1, begin + form.size())
                view.erase(edit, erase)

            # If the form is the first form in a sexp, abort.
            if form and innermost and forms.find_previous(view, point):
                sel.append(innermost.open.begin())

                if view.match_selector(
                    form.begin(), "punctuation.section.parens.begin"
                ):
                    head = forms.find_next(view, form.begin() + 1)

                    if view.substr(head) == arrow:
                        element_str = view.substr(form)
                        view.erase(edit, form)
                        enclosing = sexp.innermost(
                            view, form.begin(), edge=False
                        ).extent()
                        enclosing_str = view.substr(enclosing)
                        view.erase(edit, enclosing)
                        insert = (
                            element_str[:-1]
                            + " "
                            + indent.prune_string(enclosing_str + ")")
                        )
                        view.insert(edit, enclosing.begin(), insert)

                    else:
                        thread_unthreaded()
                else:
                    thread_unthreaded()


def thread_first(view, edit):
    thread(view, edit, "->")


def thread_last(view, edit):
    thread(view, edit, "->>")


def forward_up(view, edit):
    for region, sel in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            sel.append(innermost.close.end())


def forward_down(view, edit):
    for region, sel in iterate(view):
        open_bracket = selectors.find(view, region.begin(), selectors.SEXP_BEGIN)

        if open_bracket != -1:
            sel.append(open_bracket + 1)


def backward_up(view, edit):
    for region, sel in iterate(view):
        innermost = sexp.innermost(view, region.begin(), edge=False)

        if innermost:
            sel.append(innermost.open.begin())


def backward_down(view, edit):
    for region, sel in iterate(view):
        close_bracket = selectors.find(view, region.begin(), selectors.SEXP_END, False)

        if close_bracket != -1:
            sel.append(close_bracket)


def discard_undiscard(view, edit, scope="innermost"):
    for region, sel in iterate(view):
        point = region.begin()

        if view.match_selector(point, "comment.block"):
            hash = selectors.find(
                view,
                point,
                "punctuation.definition.comment & keyword.operator.macro",
                forward=False
            )

            if hash != -1:
                view.erase(edit, Region(hash, hash + 2))
        else:
            expression = None

            if scope == "innermost":
                expression = sexp.innermost(view, point, edge=True)
            elif scope == "outermost":
                expression = sexp.outermost(view, point, edge=True)

            if expression:
                view.insert(edit, expression.open.begin(), '#_')
