from sublime import CLASS_WORD_START, Region


OPEN = {'(': ')', '[': ']', '{': '}'}
CLOSE = {')': '(', ']': '[', '}': '{'}
MACRO_CHARACTERS = {'#', '@', '\'', '`'}


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

        if self.view.substr(begin - 1) in MACRO_CHARACTERS:
            begin = begin - 1

        return Region(begin, region.end())


def inside_string(view, point):
    return view.match_selector(
        point,
        'string - punctuation.definition.string.begin'
    )


def inside_comment(view, point):
    # FIXME
    return view.match_selector(point, 'comment')


def ignore(view, point):
    return inside_string(view, point) or inside_comment(view, point)


def find_point(view, start_point, predicate, forward=True):
    point = start_point if forward else start_point - 1
    max_size = view.size()

    while point >= 0 and point <= max_size:
        if predicate(point):
            return point

        if forward:
            point += 1
        else:
            point -= 1


def find_open(view, start_point):
    point = start_point
    stack = 0
    in_string = inside_string(view, point)

    if in_string:
        begin = find_point(view, point, lambda p: view.substr(p) == '"', forward=False)
        return view.substr(begin), Region(begin, begin + 1)

    while point > 0:
        char = view.substr(point - 1)

        if in_string:
            point -= 1
        elif char in CLOSE:
            stack += 1
            point -= 1
        elif stack > 0 and char in OPEN:
            stack -= 1
            point -= 1
        elif stack == 0 and char in OPEN:
            return char, Region(point - 1, point)
        else:
            point -= 1

    return None, None


def find_close(view, start_point, close=None):
    point = start_point
    stack = 0
    max_point = view.size()
    in_string = inside_string(view, point)

    if in_string:
        begin = find_point(view, point, lambda p: view.substr(p) == '"')
        return Region(begin, begin + 1)

    if close is None:
        return None

    while point < max_point:
        char = view.substr(point)

        if in_string:
            point += 1
        elif char == CLOSE[close]:
            stack += 1
            point += 1
        elif stack > 0 and char == close:
            stack -= 1
            point += 1
        elif stack == 0 and char == close:
            return Region(point, point + 1)
        else:
            point += 1


def move_inside(view, point, do):
    if do == False:
        return point

    if inside_string(view, point):
        return point

    next_char = view.substr(point)

    # next char is a double quote
    if next_char == '"':
        return point + 1

    # next char is a left bracket
    elif next_char in OPEN:
        return point + 1

    # previous char is a right bracket
    elif view.substr(point - 1) in CLOSE:
        return point - 1

    # previous char is a double quote
    elif view.substr(point - 1) == '"':
        return point - 1

    # next char is the hash mark of a set or anon fn
    elif next_char == '#':
        return point + 2 if view.substr(point + 1) in {'(', '{'} else point

    # next char is a quote or an at sign preceding a left paren
    elif next_char in {'\'', '@'}:
        return point + 2 if view.substr(point + 1) == '(' else point

    return point


def innermost(view, point, edge=True):
    char, open_region = find_open(
        view,
        move_inside(view, point, edge)
    )

    if char:
        close_region = find_close(
            view,
            open_region.end(),
            close=OPEN.get(char)
        )

        return Sexp(view, open_region, close_region)


def head_word(view, open_bracket):
    return view.substr(
        view.word(
            view.find_by_class(
                open_bracket.begin(),
                True,
                CLASS_WORD_START
            )
        )
    )


def outermost(view, point, edge=True, ignore={}):
    previous = find_open(view, move_inside(view, point, edge))

    while previous[0] and point >= 0:
        current = find_open(view, point)

        if previous[0] and (
            not current[0] or (ignore and head_word(view, current[1]) in ignore)
        ):
            open_region = previous[1]

            close_region = find_close(
                view,
                open_region.end(),
                close=OPEN.get(previous[0])
            )

            return Sexp(view, open_region, close_region)
        else:
            point = previous[1].begin()
            previous = current


def is_next_to_open(view, point):
    return not ignore(view, point) and (
        view.substr(point) in OPEN or
        view.substr(point) == '"' or
        view.substr(Region(point, point + 2)) == '#{' or
        view.substr(Region(point, point + 2)) == '#(' or
        view.substr(Region(point, point + 2)) == '@(' or
        view.substr(Region(point, point + 2)) == '\'('
    )


def is_next_to_close(view, point):
    return not ignore(view, point) and (
        view.substr(point) in CLOSE or
        view.substr(point - 1) in CLOSE
    )


def is_next_to_expand_anchor(view, point):
    return is_next_to_open(view, point) or is_next_to_close(view, point)


CYCLE_ORDER = {
    '(': '[',
    '[': '{',
    '{': '#{',
    '#{': '('
}


def cycle_collection_type(view, edit):
    for region in view.sel():
        sexp = innermost(view, region.begin())

        if sexp:
            open_bracket = view.substr(sexp.open)
            new_open_bracket = CYCLE_ORDER[open_bracket]
            new_close_bracket = OPEN.get(new_open_bracket[-1:])
            view.replace(edit, sexp.close, new_close_bracket)
            view.replace(edit, sexp.open, new_open_bracket)
