import sublime

LPAREN = '('
RPAREN = ')'
LBRACKET = '['
RBRACKET = ']'
LBRACE = '{'
RBRACE = '}'

LBRACKETS = {LPAREN: RPAREN, LBRACE: RBRACE, LBRACKET: RBRACKET}
RBRACKETS = {RPAREN: LPAREN, RBRACE: LBRACE, RBRACKET: LBRACKET}


def ignore(view, pos):
    in_string = view.score_selector(pos, 'string') > 0
    in_comment = view.score_selector(pos, 'comment') > 0
    return in_string or in_comment


def char_range(view, start, end):
    return view.substr(sublime.Region(start, end))


def find_lbracket(view, start_pos):
    def scan(stack, pos):
        if ignore(view, pos - 1):
            return scan(stack, pos - 1)
        else:
            char = char_range(view, pos, pos - 1)

            if pos <= 0:
                return None, None
            elif char in RBRACKETS:
                return scan(stack + 1, pos - 1)
            elif stack > 0 and char in LBRACKETS:
                return scan(stack - 1, pos - 1)
            elif stack == 0 and char in LBRACKETS:
                return char, pos - 1
            else:
                return scan(stack, pos - 1)

    return scan(0, start_pos)


def is_rbracket_of_kind(lbracket, char):
    return char in RBRACKETS and RBRACKETS[char] == lbracket


def find_rbracket(view, lbracket, start_pos):
    def scan(stack, pos):
        if ignore(view, pos):
            return scan(stack, pos + 1)
        else:
            char = char_range(view, pos, pos + 1)

            if lbracket is None:
                return None, None
            elif char == lbracket:
                return scan(stack + 1, pos + 1)
            elif stack > 0 and is_rbracket_of_kind(lbracket, char):
                return scan(stack - 1, pos + 1)
            elif stack == 0 and is_rbracket_of_kind(lbracket, char):
                return char, pos + 1
            else:
                return scan(stack, pos + 1)

    # Must start after the first lbracket so that it doesn't increment the
    # stack counter.
    return scan(0, start_pos + 1)


def current_form_region(view, pos):
    if ignore(view, pos):
        return None

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
