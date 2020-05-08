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
    in_string = view.score_selector(pos, "string") > 0
    in_comment = view.score_selector(pos, "comment") > 0
    return in_string or in_comment


def next_char(view, pos):
    return view.substr(sublime.Region(pos, pos + 1))


def prev_char(view, pos):
    return view.substr(sublime.Region(pos - 1, pos))


def find_lbracket(view, start_pos):
    def scan(stack, pos):
        if ignore(view, pos - 1):
            return scan(stack, pos - 1)
        else:
            char = prev_char(view, pos)

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
            char = next_char(view, pos)

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
    next_two_chars = view.substr(sublime.Region(pos, pos + 2))

    if next_two_chars == '#{':
        pos += 2
    elif len(next_two_chars) >= 1 and next_two_chars[0] in LBRACKETS:
        pos += 1
    elif prev_char(view, pos) in RBRACKETS:
        pos -= 1

    lbracket, lpos = find_lbracket(view, pos)

    if lbracket is not None:
        _, rpos = find_rbracket(view, lbracket, lpos)

        if prev_char(view, lpos) == '#':
            lpos -= 1

        return sublime.Region(lpos, rpos)
    else:
        return None
