import sublime

LPAREN = '('
RPAREN = ')'
LBRACKET = '['
RBRACKET = ']'
LBRACE = '{'
RBRACE = '}'

LBRACKETS = {LPAREN: RPAREN, LBRACE: RBRACE, LBRACKET: RBRACKET}
RBRACKETS = {RPAREN: LPAREN, RBRACE: LBRACE, RBRACKET: LBRACKET}


def point_inside_regions(point, regions):
    for region in regions:
        if point > region.begin() and point < region.end():
            return region


def inside_string(view, point):
    return (
        view.match_selector(point, 'string') and
        point_inside_regions(point, view.find_by_selector('string'))
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
    lbracket = None, None

    while point > 0:
        char = char_range(view, point, point - 1)

        if ignore(view, point - 1):
            point -= 1
            continue
        elif point <= 0:
            break
        elif char in RBRACKETS:
            stack += 1
            point -= 1
            continue
        elif stack > 0 and char in LBRACKETS:
            stack -= 1
            point -= 1
            continue
        elif stack == 0 and char in LBRACKETS:
            lbracket = char, point - 1
            break
        else:
            point -= 1
            continue

    return lbracket


def is_rbracket_of_kind(lbracket, char):
    return char in RBRACKETS and RBRACKETS[char] == lbracket


def find_rbracket(view, lbracket, start_point):
    point = start_point + 1
    stack = 0
    rbracket = None, None
    max_point = view.size()

    if lbracket is None:
        return rbracket

    while point < max_point:
        char = char_range(view, point, point + 1)

        if ignore(view, point):
            point += 1
            continue
        elif char == lbracket:
            stack += 1
            point += 1
            continue
        elif stack > 0 and is_rbracket_of_kind(lbracket, char):
            stack -= 1
            point += 1
            continue
        elif stack == 0 and is_rbracket_of_kind(lbracket, char):
            rbracket = char, point + 1
            break
        else:
            point += 1
            continue

    return rbracket


def current_form_region(view, point):
    next_char = char_range(view, point, point + 1)

    # next char is a left bracket
    if next_char in LBRACKETS:
        point += 1

    # previous char is a right bracket
    elif char_range(view, point, point - 1) in RBRACKETS:
        point -= 1

    # next char is the hash mark of a set or anon fn
    elif next_char == '#':
        nnext_char = char_range(view, point + 1, point + 2)

        if nnext_char == '(' or nnext_char == '{':
            point += 2

    # next char is an at sign preceding a left paren
    elif next_char == '@':
        nnext_char = char_range(view, point + 1, point + 2)

        if nnext_char == '(':
            point += 2

    lbracket, lpoint = find_lbracket(view, point)

    if lbracket is not None:
        _, rpoint = find_rbracket(view, lbracket, lpoint)

        prev_char = char_range(view, lpoint, lpoint - 1)

        if prev_char == '#' or prev_char == '@':
            lpoint -= 1

        return sublime.Region(lpoint, rpoint)
    else:
        return None


def is_next_to_expand_anchor(view, point):
    return (
        char_range(view, point, point + 1) in LBRACKETS or
        char_range(view, point, point + 1) in RBRACKETS or
        char_range(view, point, point + 2) == '#{' or
        char_range(view, point, point + 2) == '#(' or
        char_range(view, point, point + 2) == '@(' or
        char_range(view, point, point - 1) in RBRACKETS
    )
