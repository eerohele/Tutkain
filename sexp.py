from sublime import CLASS_PUNCTUATION_START, CLASS_WORD_START, Region


OPEN = {'(': ')', '[': ']', '{': '}'}
CLOSE = {')': '(', ']': '[', '}': '{'}


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


def find_open(view, start_point):
    point = start_point
    stack = 0
    in_string = inside_string(view, point)

    if in_string:
        begin = view.find_by_class(point, False, CLASS_PUNCTUATION_START)
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
        begin = view.find_by_class(point, True, CLASS_PUNCTUATION_START)
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


def absorb_macro_characters(view, region, absorb=False):
    if absorb and view.substr(region.begin() - 1) in {'#', '@', '\'', '`'}:
        return Region(region.begin() - 1, region.end())
    else:
        return Region(region.begin(), region.end())


def innermost(view, point, absorb=False, edge=True):
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

        return absorb_macro_characters(
            view,
            Region(open_region.begin(), close_region.end()),
            absorb=absorb
        )


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


def outermost(view, point, edge=True, absorb=False, ignore={}):
    previous = find_open(view, move_inside(view, point, edge))

    while previous[0] and point >= 0:
        current = find_open(view, point)

        if previous[0] and (
            not current[0] or (ignore and head_word(view, current[1]) in ignore)
        ):
            close_bracket = find_close(
                view,
                previous[1].end(),
                close=OPEN.get(previous[0])
            )

            return absorb_macro_characters(
                view,
                Region(previous[1].begin(), close_bracket.end()),
                absorb=absorb
            )
        else:
            point = previous[1].begin()
            previous = current


def current(view, point):
    return outermost(view, point, absorb=True, ignore={'comment'})


def is_next_to_expand_anchor(view, point):
    return (
        view.substr(point) in OPEN or
        view.substr(point) in CLOSE or
        view.substr(point) == '"' or
        view.substr(Region(point, point + 2)) == '#{' or
        view.substr(Region(point, point + 2)) == '#(' or
        view.substr(Region(point, point + 2)) == '@(' or
        view.substr(Region(point, point + 2)) == '\'(' or
        view.substr(point - 1) in CLOSE
    )


cycle_order = {
    '(': '[',
    '[': '{',
    '{': '#{',
    '#{': '('
}


def cycle_collection_type(view, edit):
    for region in view.sel():
        sexp = innermost(view, region.begin(), absorb=False)

        if sexp:
            begin = sexp.begin()

            # This is quite ugly. There's probably an elegant abstraction here
            # somewhere, I just haven't found it yet.
            if view.substr(Region(begin - 1, begin + 1)) == '#{':
                open_bracket = '#{'
                begin -= 1
            else:
                open_bracket = view.substr(begin)

            new_open_bracket = cycle_order[open_bracket]
            new_close_bracket = OPEN.get(new_open_bracket[-1:])
            open_region = Region(begin, begin + len(open_bracket))

            view.replace(edit, open_region, new_open_bracket)

            # This is slower than calculating the new position, but the
            # implementation is *much* simpler.
            close_region = find_close(
                view,
                begin + len(new_open_bracket),
                close=OPEN.get(open_bracket[-1:])
            )

            view.replace(edit, close_region, new_close_bracket)
