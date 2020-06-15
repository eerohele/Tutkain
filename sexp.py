import re
from sublime import CLASS_WORD_START, Region


OPEN = {'(': ')', '[': ']', '{': '}'}
CLOSE = {')': '(', ']': '[', '}': '{'}
MACRO_CHARACTERS = {'#', '@', '\'', '`', '^'}


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

    def __eq__(self, other):
        return other and self.extent() == other.extent()


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


def has_begin_double_quote(view, point):
    return view.match_selector(
        point,
        'punctuation.definition.string.begin - constant.character.escape'
    )


def has_end_double_quote(view, point):
    return view.match_selector(
        point,
        'punctuation.definition.string.end - constant.character.escape'
    )


def find_open(view, start_point):
    point = start_point
    stack = 0

    if inside_string(view, point):
        begin = find_point(view, point, lambda point: has_begin_double_quote(view, point), forward=False)
        return view.substr(begin), Region(begin, begin + 1)

    while point > 0:
        char = view.substr(point - 1)

        if inside_string(view, point):
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

    if inside_string(view, point):
        end = find_point(view, point, lambda point: has_end_double_quote(view, point))
        return Region(end, end + 1)

    if close is None:
        return None

    while point < max_point:
        char = view.substr(point)

        if inside_string(view, point):
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
    if not do:
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

    # next char is the hash mark of a set or anon fn or the metadata marker
    elif next_char in {'#', '^'}:
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
        view.substr(Region(point, point + 2)) == '^{' or
        view.substr(Region(point, point + 2)) == '#(' or
        view.substr(Region(point, point + 2)) == '@(' or
        view.substr(Region(point, point + 2)) == '\'('
    )


def is_next_to_close(view, point):
    return not ignore(view, point) and (
        view.substr(point) in CLOSE or
        view.substr(point - 1) in CLOSE
    )


def is_insignificant(view, point):
    return re.match(r'[\s,]', view.substr(point))


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
    if ignore(view, point):
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

    while begin > 0:
        if ((view.match_selector(begin - 1, selector) and view.match_selector(begin, selector)) or
            # account for shorthand meta notation (^:foo)
            (view.match_selector(begin - 1, 'keyword.operator.macro') and
             view.match_selector(begin, 'constant.other.keyword'))):
            begin -= 1
        else:
            break

    while end < max_size:
        if (view.match_selector(end, 'keyword.operator.macro') and
            # account for shorthand meta notation (^:foo)
           view.match_selector(end + 1, 'constant.other.keyword')):
            selector = 'constant.other.keyword'
            end += 2
        elif (view.match_selector(end - 1, selector) and not view.match_selector(end, selector)):
            break
        else:
            end += 1

    return Region(begin, end)


RE_SYMBOL_CHARACTERS = r'[\w\*\+\!\-\_\'\?\<\>\=\/\.]'


def is_symbol_character(view, point):
    return re.match(RE_SYMBOL_CHARACTERS, view.substr(point))


def extract_symbol(view, point):
    begin = end = point
    max_size = view.size()

    while begin > 0:
        if not is_symbol_character(view, begin - 1) and is_symbol_character(view, begin):
            break
        else:
            begin -= 1

    while end < max_size:
        if is_symbol_character(view, end - 1) and not is_symbol_character(view, end):
            break
        else:
            end += 1

    return Region(begin, end)


def adjacent_element_direction(view, point):
    if not ignore(view, point) and re.match(r'[^\s,\)\]\}\x00]', view.substr(point)):
        return 1
    elif not ignore(view, point - 1) and re.match(r'[^\s,\(\[\{\x00]', view.substr(point - 1)):
        return -1
    else:
        return 0


def find_adjacent_element(view, point):
    direction = adjacent_element_direction(view, point)

    if direction == 1:
        return find_next_element(view, point)
    elif direction == -1:
        return find_previous_element(view, point)
    else:
        return None


# TODO: The conditional logic here is a bit convoluted. Can we make it more straightforward?
def find_next_element(view, point):
    max_size = view.size()

    while point < max_size:
        if has_end_double_quote(view, point) or (
            not ignore(view, point) and view.substr(point) in CLOSE
        ):
            return None
        elif is_insignificant(view, point):
            point += 1
        elif is_next_to_open(view, point):
            return innermost(view, point).extent()
        else:
            scope = extract_scope(view, point)

            if scope:
                return scope
            elif is_symbol_character(view, point):
                return extract_symbol(view, point)
            else:
                return None


def find_previous_element(view, point):
    while point > 0:
        if has_begin_double_quote(view, point - 1) or (
            not ignore(view, point) and view.substr(point - 1) in OPEN
        ):
            return None
        elif is_insignificant(view, point - 1):
            point -= 1
        elif view.substr(point - 1) in CLOSE or view.substr(point - 1) == '"':
            return innermost(view, point).extent()
        else:
            scope = extract_scope(view, point - 1)

            if scope:
                return scope
            elif is_symbol_character(view, point - 1):
                return extract_symbol(view, point)
            else:
                return None


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
