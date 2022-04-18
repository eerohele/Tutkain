import re
from . import sexp
from . import selectors
from sublime import CLASS_WORD_START, CLASS_WORD_END, Region


def head_word(view, point):
    return view.substr(view.word(view.find_by_class(point, True, CLASS_WORD_START)))


def adjacent_direction(view, point):
    # TODO: Use view.match_selector() instead.
    if re.match(r"[^\s,\)\]\}\x00]", view.substr(point)):
        return 1
    elif re.match(r"[^\s,\(\[\{\x00]", view.substr(point - 1)):
        return -1
    else:
        return 0


def find_adjacent(view, point):
    """Given a View and a point, return the Clojure form adjacent to the point,
    if any.

    If there is a Clojure form both to the left and to the right of the point,
    return the one to the left. If there is no form adjacent to the point,
    return None."""
    if selectors.ignore(view, point):
        return None

    direction = adjacent_direction(view, point)

    if direction == 1:
        return find_next(view, point)
    elif direction == -1:
        return find_previous(view, point)
    else:
        return None


def find_next(view, point):
    """Given a View and a point, return the next Clojure form to the right of
    the point."""
    max_point = view.size()

    if view.match_selector(point, "string - punctuation.definition.string.begin | comment.line"):
        return view.word(view.find_by_class(point, True, CLASS_WORD_END))
    else:
        while point < max_point:
            if view.match_selector(point, selectors.SEXP_END):
                return None
            elif view.match_selector(point, selectors.SEXP_BEGIN):
                return sexp.innermost(view, point, edge="forward").extent()
            elif (
                view.match_selector(point, "keyword.operator.macro")
                and view.substr(point) != "^"
                and view.match_selector(point + 1, "punctuation.definition.keyword")
            ):
                begin = selectors.find(view, point, selectors.SEXP_BEGIN)
                return sexp.innermost(view, begin).extent()
            elif view.match_selector(point, "keyword.operator.macro"):
                begin = selectors.find(
                    view, point, selectors.SEXP_BEGIN + " | meta.reader-form"
                )

                if view.match_selector(begin, selectors.SEXP_BEGIN):
                    return sexp.innermost(view, begin).extent()
                else:
                    dispatch = Region(point, point + 1)
                    form = selectors.expand_by_selector(view, begin, "meta.reader-form")
                    return form.cover(dispatch)
            elif view.match_selector(point, "meta.reader-form"):
                return selectors.expand_by_selector(view, point, "meta.reader-form | keyword.operator.macro")
            else:
                point += 1


def absorb_macro_characters(view, region):
    """Given a View and a Region, if a macro character precedes the region,
    expand the region to cover all macro characters preceding the region.

    A macro character is a character that matches the `keyword.operator.macro`
    scope."""
    if view.match_selector(region.begin() - 1, "keyword.operator.macro"):
        keywords = selectors.expand_by_selector(
            view, region.begin() - 1, "keyword.operator.macro"
        )
        return keywords.cover(region)
    else:
        return region


def find_previous(view, point):
    """Given a View and a point, return the previous Clojure form to the right
    of the point."""
    if view.match_selector(point, "string - punctuation.definition.string.begin | comment.line"):
        return view.word(view.find_by_class(point, False, CLASS_WORD_START))
    else:
        while point > 0:
            if view.match_selector(point - 1, selectors.SEXP_BEGIN):
                return None
            elif view.match_selector(point - 1, selectors.SEXP_END):
                innermost = sexp.innermost(view, point, edge="backward").extent()
                return absorb_macro_characters(view, innermost)
            elif view.match_selector(point - 1, "meta.reader-form"):
                form = selectors.expand_by_selector(view, point - 1, "meta.reader-form")
                return absorb_macro_characters(view, form)
            else:
                point -= 1


def seek_forward(view, start_point, pred):
    point = start_point

    while point <= view.size():
        form = find_next(view, point)

        if pred(form):
            return form
        else:
            point = form.end()


def seek_backward(view, start_point, pred):
    point = start_point

    while point >= 0:
        form = find_previous(view, point)

        if form is None:
            return Region(0, 0)
        elif pred(form):
            return form
        else:
            point = form.begin()
