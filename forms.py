import re
from . import sexp
from . import selectors
from sublime import CLASS_WORD_START, CLASS_WORD_END, Region


def head_word(view, point):
    return view.substr(view.word(view.find_by_class(point, True, CLASS_WORD_START)))


def adjacent_direction(view, point):
    # TODO: Use view.match_selector() instead.
    if re.match(r'[^\s,\)\]\}\x00]', view.substr(point)):
        return 1
    elif re.match(r'[^\s,\(\[\{\x00]', view.substr(point - 1)):
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


SELECTOR = 'meta.reader-form | meta.metadata | meta.quoted | meta.deref'


def find_next(view, point):
    max_point = view.size()

    if selectors.inside_string(view, point):
        return view.word(view.find_by_class(point, True, CLASS_WORD_END))
    else:
        while point <= max_point:
            if view.match_selector(point, 'meta.sexp.end'):
                return None
            elif view.match_selector(point, 'meta.sexp.begin | meta.sexp.prefix'):
                return sexp.innermost(view, point).extent()
            elif view.match_selector(point, SELECTOR):
                return selectors.expand_by_selector(view, point, SELECTOR)
            else:
                point += 1


def find_previous(view, point):
    if selectors.inside_string(view, point):
        return view.word(view.find_by_class(point, False, CLASS_WORD_START))
    else:
        while point > 0:
            if view.match_selector(point - 1, 'meta.sexp.begin | meta.sexp.prefix'):
                return None
            elif view.match_selector(point - 1, 'meta.sexp.end'):
                return sexp.innermost(view, point).extent()
            elif view.match_selector(point - 1, SELECTOR):
                return selectors.expand_by_selector(view, point - 1, SELECTOR)
            else:
                point -= 1
