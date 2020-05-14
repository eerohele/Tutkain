import sublime

LPAREN = '('
RPAREN = ')'
LBRACKET = '['
RBRACKET = ']'
LBRACE = '{'
RBRACE = '}'

LBRACKETS = {LPAREN: RPAREN, LBRACE: RBRACE, LBRACKET: RBRACKET}
RBRACKETS = {RPAREN: LPAREN, RBRACE: LBRACE, RBRACKET: LBRACKET}


def point_inside_regions(pos, regions):
    for region in regions:
        if pos > region.begin() and pos < region.end():
            return region


def inside_string(view, pos):
    return (
        view.match_selector(pos, 'string') and
        point_inside_regions(pos, view.find_by_selector('string'))
    )


def inside_comment(view, pos):
    # FIXME
    return view.match_selector(pos, 'comment')


def ignore(view, pos):
    return inside_string(view, pos) or inside_comment(view, pos)


def char_range(view, start, end):
    return view.substr(sublime.Region(start, end))


def find_lbracket(view, start_pos):
    pos = start_pos
    stack = 0
    lbracket = None, None

    while pos > 0:
        char = char_range(view, pos, pos - 1)

        if ignore(view, pos - 1):
            pos -= 1
            continue
        elif pos <= 0:
            break
        elif char in RBRACKETS:
            stack += 1
            pos -= 1
            continue
        elif stack > 0 and char in LBRACKETS:
            stack -= 1
            pos -= 1
            continue
        elif stack == 0 and char in LBRACKETS:
            lbracket = char, pos - 1
            break
        else:
            pos -= 1
            continue

    return lbracket


def is_rbracket_of_kind(lbracket, char):
    return char in RBRACKETS and RBRACKETS[char] == lbracket


def find_rbracket(view, lbracket, start_pos):
    pos = start_pos + 1
    stack = 0
    rbracket = None, None
    max_pos = view.size()

    if lbracket is None:
        return rbracket

    while pos < max_pos:
        char = char_range(view, pos, pos + 1)

        if ignore(view, pos):
            pos += 1
            continue
        elif char == lbracket:
            stack += 1
            pos += 1
            continue
        elif stack > 0 and is_rbracket_of_kind(lbracket, char):
            stack -= 1
            pos += 1
            continue
        elif stack == 0 and is_rbracket_of_kind(lbracket, char):
            rbracket = char, pos + 1
            break
        else:
            pos += 1
            continue

    return rbracket


def current_form_region(view, pos):
    next_char = char_range(view, pos, pos + 1)

    # next char is a left bracket
    if next_char in LBRACKETS:
        pos += 1

    # previous char is a right bracket
    elif char_range(view, pos, pos - 1) in RBRACKETS:
        pos -= 1

    # next char is the hash mark of a set or anon fn
    elif next_char == '#':
        nnext_char = char_range(view, pos + 1, pos + 2)

        if nnext_char == '(' or nnext_char == '{':
            pos += 2

    # next char is an at sign preceding a left paren
    elif next_char == '@':
        nnext_char = char_range(view, pos + 1, pos + 2)

        if nnext_char == '(':
            pos += 2

    lbracket, lpos = find_lbracket(view, pos)

    if lbracket is not None:
        _, rpos = find_rbracket(view, lbracket, lpos)

        prev_char = char_range(view, lpos, lpos - 1)

        if prev_char == '#' or prev_char == '@':
            lpos -= 1

        return sublime.Region(lpos, rpos)
    else:
        return None


def is_next_to_expand_anchor(view, pos):
    return (
        char_range(view, pos, pos + 1) in LBRACKETS or
        char_range(view, pos, pos + 1) in RBRACKETS or
        char_range(view, pos, pos + 2) == '#{' or
        char_range(view, pos, pos + 2) == '#(' or
        char_range(view, pos, pos + 2) == '@(' or
        char_range(view, pos, pos - 1) in RBRACKETS
    )
