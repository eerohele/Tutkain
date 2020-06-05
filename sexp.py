from sublime import CLASS_WORD_START, Region


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


def find_open_bracket(view, start_point):
    point = start_point
    stack = 0

    while point > 0:
        char = view.substr(point - 1)

        if ignore(view, point):
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


def find_close_bracket(view, close_bracket, start_point):
    point = start_point
    stack = 0
    max_point = view.size()

    if close_bracket is None:
        return None

    while point < max_point:
        char = view.substr(point)

        if ignore(view, point):
            point += 1
        elif char == CLOSE[close_bracket]:
            stack += 1
            point += 1
        elif stack > 0 and char == close_bracket:
            stack -= 1
            point += 1
        elif stack == 0 and char == close_bracket:
            return Region(point, point + 1)
        else:
            point += 1


def into_adjacent(view, point):
    if inside_string(view, point):
        return point

    next_char = view.substr(point)

    # next char is a left bracket
    if next_char in OPEN:
        return point + 1

    # previous char is a right bracket
    elif view.substr(point - 1) in CLOSE:
        return point - 1

    # next char is the hash mark of a set or anon fn
    elif next_char == '#':
        return point + 2 if view.substr(point + 1) in {'(', '{'} else point

    # next char is a quote or an at sign preceding a left paren
    elif next_char in {'\'', '@'}:
        return point + 2 if view.substr(point + 1) == '(' else point

    return point


def absorb_macro_characters(view, point, absorb=False):
    if absorb and view.substr(point - 1) in {'#', '@', '\'', '`'}:
        return point - 1
    else:
        return point


def innermost(view, point, absorb=False):
    char, region = find_open_bracket(view, point)

    if char:
        close_region = find_close_bracket(
            view,
            OPEN[char],
            region.end()
        )

        begin = absorb_macro_characters(
            view,
            region.begin(),
            absorb=absorb
        )

        return Region(begin, close_region.end())


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


def outermost(view, point, absorb=False, ignore={}):
    previous = find_open_bracket(view, point)

    while previous[0] and point >= 0:
        current = find_open_bracket(view, point)

        if previous[0] and (
            not current[0] or (ignore and head_word(view, current[1]) in ignore)
        ):
            close_bracket = find_close_bracket(
                view,
                OPEN[previous[0]],
                previous[1].end()
            )

            begin = absorb_macro_characters(
                view,
                previous[1].begin(),
                absorb=absorb
            )

            return Region(begin, close_bracket.end())
        else:
            point = previous[1].begin()
            previous = current


def is_next_to_expand_anchor(view, point):
    return (
        view.substr(point) in OPEN or
        view.substr(point) in CLOSE or
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
        sexp = innermost(
            view,
            # TODO: Need to figure out a better idiom for this.
            into_adjacent(view, region.begin()),
            absorb=False
        )

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
            new_close_bracket = OPEN[new_open_bracket[-1:]]
            open_region = Region(begin, begin + len(open_bracket))

            view.replace(edit, open_region, new_open_bracket)

            # This is slower than calculating the new position, but the
            # implementation is *much* simpler.
            close_region = find_close_bracket(
                view,
                OPEN[open_bracket[-1:]],
                begin + len(new_open_bracket)
            )

            view.replace(edit, close_region, new_close_bracket)
