import sublime
LBRACKETS = {'(': ')', '[': ']', '{': '}'}
RBRACKETS = {')': '(', ']': '[', '}': '{'}


def inside_string(view, point):
    return (
        view.match_selector(point, 'string')
        and not view.match_selector(
            point,
            'punctuation.definition.string.begin'
        )
    )


def inside_comment(view, point):
    # FIXME
    return view.match_selector(point, 'comment')


def ignore(view, point):
    return inside_string(view, point) or inside_comment(view, point)


def char_range(view, start, end):
    return view.substr(sublime.Region(start, end))


def find_lbracket(view, start_point):
    point = start_point
    stack = 0

    while point > 0:
        char = char_range(view, point, point - 1)

        if ignore(view, point):
            point -= 1
        elif char in RBRACKETS:
            stack += 1
            point -= 1
        elif stack > 0 and char in LBRACKETS:
            stack -= 1
            point -= 1
        elif stack == 0 and char in LBRACKETS:
            return char, point - 1
        else:
            point -= 1

    return None, None


def find_rbracket_point(view, lbracket, start_point):
    point = start_point
    stack = 0
    max_point = view.size()

    if lbracket is None:
        return None

    while point < max_point:
        char = char_range(view, point, point + 1)

        if ignore(view, point):
            point += 1
        elif char == RBRACKETS[lbracket]:
            stack += 1
            point += 1
        elif stack > 0 and char == lbracket:
            stack -= 1
            point += 1
        elif stack == 0 and char == lbracket:
            return point + 1
        else:
            point += 1


def calculate_start_point(view, point):
    next_char = char_range(view, point, point + 1)

    # next char is a left bracket
    if next_char in LBRACKETS:
        return point + 1

    # previous char is a right bracket
    elif char_range(view, point, point - 1) in RBRACKETS:
        return point - 1

    # next char is the hash mark of a set or anon fn
    elif next_char == '#':
        nnext_char = char_range(view, point + 1, point + 2)
        return point + 2 if nnext_char in {'(', '{'} else point

    # next char is a quote or an at sign preceding a left paren
    elif next_char in {'\'', '@'}:
        nnext_char = char_range(view, point + 1, point + 2)
        return point + 2 if nnext_char == '(' else point

    return point


def current_form_region(view, point):
    start_point = calculate_start_point(view, point)
    lbracket, lpoint = find_lbracket(view, start_point)

    if lbracket:
        rpoint = find_rbracket_point(view, LBRACKETS[lbracket], lpoint + 1)

        if char_range(view, lpoint, lpoint - 1) in {'#', '@', '\''}:
            return sublime.Region(lpoint - 1, rpoint)
        else:
            return sublime.Region(lpoint, rpoint)


def is_next_to_expand_anchor(view, point):
    return (
        char_range(view, point, point + 1) in LBRACKETS or
        char_range(view, point, point + 1) in RBRACKETS or
        char_range(view, point, point + 2) == '#{' or
        char_range(view, point, point + 2) == '#(' or
        char_range(view, point, point + 2) == '@(' or
        char_range(view, point, point + 2) == '\'(' or
        char_range(view, point, point - 1) in RBRACKETS
    )
