import re
from sublime import CLASS_WORD_START, CLASS_WORD_END, Region


OPEN = {'(': ')', '[': ']', '{': '}'}
CLOSE = {')': '(', ']': '[', '}': '{'}
RE_NON_SYMBOL_CHARACTERS = r'[\s,\(\[\{\)\]\}\"\x00]'


class Sexp():
    def __init__(self, view, open_region, close_region):
        self.view = view
        self.open = self.absorb_macro_characters(open_region)
        self.close = close_region

    def __str__(self):
        return self.view.substr(self.extent())

    def extent(self):
        return Region(self.open.begin(), self.close.end())

    def is_empty(self):
        return self.open.end() == self.close.begin()

    def contains(self, point):
        return point >= self.open.end() and point <= self.close.begin()

    def absorb_macro_characters(self, region):
        begin = region.begin()

        if self.view.match_selector(
            begin - 1,
            'meta.sexp.prefix | meta.quoted.begin | meta.metadata.begin'
        ):
            # Find the first point that contains a character other than a macro character
            boundary = find_by_selector(
                self.view,
                begin - 1,
                '(- meta.sexp.prefix & - meta.quoted.begin & - meta.metadata.begin)',
                forward=False
            ) + 1

            begin = max(boundary, 0)

        return Region(begin, region.end())

    def __eq__(self, other):
        return other and self.extent() == other.extent()


def inside_string(view, point):
    return view.match_selector(point, 'string - punctuation.definition.string.begin')


def inside_comment(view, point):
    return view.match_selector(point, 'comment.line')


def ignore(view, point):
    return view.match_selector(
        point,
        'string - punctuation.definition.string.begin | comment.line'
    )


def find_by_selector(view, start_point, selector, forward=True):
    point = start_point if forward else start_point - 1
    max_size = view.size()

    while point >= 0 and point <= max_size:
        if view.match_selector(point, selector):
            return point

        if forward:
            point += 1
        else:
            point -= 1

    return -1


def find_open(view, start_point):
    point = start_point
    stack = 0

    while point > 0:
        char = view.substr(point - 1)

        if char in CLOSE and not ignore(view, point - 1):
            stack += 1
            point -= 1
        elif stack > 0 and char in OPEN and not ignore(view, point - 1):
            stack -= 1
            point -= 1
        elif stack == 0 and char in OPEN and not ignore(view, point - 1):
            return char, Region(point - 1, point)
        else:
            point -= 1

    return None, None


def find_close(view, start_point, close=None):
    point = start_point
    stack = 0
    max_point = view.size()

    if close is None:
        return None

    while point < max_point:
        char = view.substr(point)

        if char == CLOSE[close] and not ignore(view, point):
            stack += 1
            point += 1
        elif stack > 0 and char == close and not ignore(view, point):
            stack -= 1
            point += 1
        elif stack == 0 and char == close and not ignore(view, point):
            return Region(point, point + 1)
        else:
            point += 1


def move_inside(view, point, edge):
    if not edge or inside_string(view, point):
        return point
    elif view.match_selector(
        point,
        'meta.sexp.begin | meta.sexp.prefix | meta.quoted.begin | meta.metadata.begin'
    ):
        return view.find(r'[\(\[\{\"]', point).end()
    elif view.match_selector(point - 1, 'meta.sexp.end'):
        return point - 1
    else:
        return point


def innermost(view, start_point, edge=True):
    point = move_inside(view, start_point, edge)

    if inside_comment(view, point):
        return None
    elif inside_string(view, point):
        begin = find_by_selector(
            view,
            point,
            'punctuation.definition.string.begin - constant.character.escape',
            forward=False
        )

        end = find_by_selector(
            view,
            point,
            'punctuation.definition.string.end - constant.character.escape'
        )

        # TODO: Is a string a sexp?
        return Sexp(view, Region(begin, begin + 1), Region(end, end + 1))
    else:
        char, open_region = find_open(view, point)

        if char:
            close_region = find_close(
                view,
                open_region.end(),
                close=OPEN.get(char)
            )

            return Sexp(view, open_region, close_region)


def walk_outward(view, point):
    sexp = innermost(view, point, edge=False)

    while sexp:
        yield sexp
        sexp = innermost(view, sexp.open.begin(), edge=False)


def head_word(view, point):
    return view.substr(view.word(view.find_by_class(point, True, CLASS_WORD_START)))


def outermost(view, point, edge=True, ignore={}):
    previous = find_open(view, move_inside(view, point, edge))

    while previous[0] and point >= 0:
        current = find_open(view, point)

        if previous[0] and (
            not current[0] or (ignore and head_word(view, current[1].begin()) in ignore)
        ):
            open_region = previous[1]
            close_region = find_close(view, open_region.end(), close=OPEN.get(previous[0]))
            return Sexp(view, open_region, close_region)
        else:
            point = previous[1].begin()
            previous = current


def adjacent_element_direction(view, point):
    if re.match(r'[^\s,\)\]\}\x00]', view.substr(point)):
        return 1
    elif re.match(r'[^\s,\(\[\{\x00]', view.substr(point - 1)):
        return -1
    else:
        return 0


def find_adjacent_element(view, point):
    if ignore(view, point):
        return None

    direction = adjacent_element_direction(view, point)

    if direction == 1:
        return find_next_element(view, point)
    elif direction == -1:
        return find_previous_element(view, point)
    else:
        return None


SELECTOR = 'meta.reader-form | meta.metadata | meta.quoted | meta.deref'


def expand_by_selector(view, start_point, selector):
    point = start_point
    max_point = view.size()
    begin = 0
    end = max_point

    while point > 0:
        if view.match_selector(point, selector) and not view.match_selector(point - 1, selector):
            begin = point
            break
        else:
            point -= 1

    while point < max_point:
        if view.match_selector(point - 1, selector) and not view.match_selector(point, selector):
            end = point
            break
        else:
            point += 1

    return Region(begin, end)


def find_next_element(view, point):
    max_point = view.size()

    if inside_string(view, point):
        return view.word(view.find_by_class(point, True, CLASS_WORD_END))
    else:
        while point <= max_point:
            if view.match_selector(point, 'meta.sexp.end'):
                return None
            elif view.match_selector(point, 'meta.sexp.begin | meta.sexp.prefix'):
                return innermost(view, point).extent()
            elif view.match_selector(point, SELECTOR):
                return expand_by_selector(view, point, SELECTOR)
            else:
                point += 1


def find_previous_element(view, point):
    if inside_string(view, point):
        return view.word(view.find_by_class(point, False, CLASS_WORD_START))
    else:
        while point > 0:
            if view.match_selector(point - 1, 'meta.sexp.begin | meta.sexp.prefix'):
                return None
            elif view.match_selector(point - 1, 'meta.sexp.end'):
                return innermost(view, point).extent()
            elif view.match_selector(point - 1, SELECTOR):
                return expand_by_selector(view, point - 1, SELECTOR)
            else:
                point -= 1


CYCLE_ORDER = {
    '(': '[',
    '[': '{',
    '{': '#{',
    '#{': '('
}


def cycle_collection_type(view, edit):
    for region in view.sel():
        point = region.begin()

        if not ignore(view, point):
            if view.match_selector(point, 'string') or view.match_selector(point - 1, 'string'):
                edge = False
            else:
                edge = True

            sexp = innermost(view, point, edge=edge)

            if sexp:
                open_bracket = view.substr(sexp.open)
                new_open_bracket = CYCLE_ORDER[open_bracket]

                if new_open_bracket[-1:] in OPEN:
                    new_close_bracket = OPEN[new_open_bracket[-1:]]
                    view.replace(edit, sexp.close, new_close_bracket)
                    view.replace(edit, sexp.open, new_open_bracket)
