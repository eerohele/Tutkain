import sublime

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
            return char, sublime.Region(point - 1, point)
        else:
            point -= 1

    return None, None


def find_close_bracket(view, open_bracket, start_point):
    point = start_point
    stack = 0
    max_point = view.size()

    if open_bracket is None:
        return None

    while point < max_point:
        char = view.substr(point)

        if ignore(view, point):
            point += 1
        elif char == CLOSE[open_bracket]:
            stack += 1
            point += 1
        elif stack > 0 and char == open_bracket:
            stack -= 1
            point += 1
        elif stack == 0 and char == open_bracket:
            return sublime.Region(point, point + 1)
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

        return sublime.Region(begin, close_region.end())


def head_word(view, open_bracket):
    return view.substr(
        view.word(
            view.find_by_class(
                open_bracket.begin(),
                True,
                sublime.CLASS_WORD_START
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

            return sublime.Region(begin, close_bracket.end())
        else:
            point = previous[1].begin()
            previous = current


def is_next_to_expand_anchor(view, point):
    return (
        view.substr(point) in OPEN or
        view.substr(point) in CLOSE or
        view.substr(sublime.Region(point, point + 2)) == '#{' or
        view.substr(sublime.Region(point, point + 2)) == '#(' or
        view.substr(sublime.Region(point, point + 2)) == '@(' or
        view.substr(sublime.Region(point, point + 2)) == '\'(' or
        view.substr(point - 1) in CLOSE
    )
