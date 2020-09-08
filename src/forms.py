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
    max_point = view.size()

    if selectors.inside_string(view, point):
        return view.word(view.find_by_class(point, True, CLASS_WORD_END))
    else:
        while point <= max_point:
            if view.match_selector(point, "meta.sexp.end"):
                return None
            elif view.match_selector(point, "meta.sexp.begin"):
                return sexp.innermost(view, point).extent()
            elif view.match_selector(point, "keyword.operator.macro"):
                begin = selectors.find(
                    view, point, "meta.sexp.begin | meta.reader-form"
                )
                dispatch = Region(point, point + 1)

                if view.match_selector(begin, "meta.sexp.begin"):
                    innermost = sexp.innermost(view, begin).extent()
                    return innermost.cover(dispatch)
                else:
                    form = selectors.expand_by_selector(view, begin, "meta.reader-form")
                    return form.cover(dispatch)
            elif view.match_selector(point, "meta.reader-form"):
                return selectors.expand_by_selector(view, point, "meta.reader-form")
            else:
                point += 1


def absorb_macro_characters(view, region):
    """Given a region, if the region is preceded by a macro character, expand the region to cover
    all macro characters preceding the region."""
    if view.match_selector(region.begin() - 1, "keyword.operator.macro"):
        keywords = selectors.expand_by_selector(
            view, region.begin() - 1, "keyword.operator.macro"
        )
        return keywords.cover(region)
    else:
        return region


def find_previous(view, point):
    if selectors.inside_string(view, point):
        return view.word(view.find_by_class(point, False, CLASS_WORD_START))
    else:
        while point > 0:
            if view.match_selector(point - 1, "meta.sexp.begin"):
                return None
            elif view.match_selector(point - 1, "meta.sexp.end"):
                innermost = sexp.innermost(view, point).extent()
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
