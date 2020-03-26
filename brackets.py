LPAREN = '('
RPAREN = ')'
LBRACKET = '['
RBRACKET = ']'
LBRACE = '{'
RBRACE = '}'

BRACKETS = {LPAREN: RPAREN, LBRACE: RBRACE, LBRACKET: RBRACKET}


def find_rbracket(ignore, lbracket, rbracket, chars, pos):
    def seek(chars, stack, pos):
        if pos >= len(chars):
            return None
        elif ignore(pos):
            return seek(chars, stack, pos + 1)
        elif chars[pos] == rbracket and stack == 0:
            return pos
        elif chars[pos] == rbracket and stack > 0:
            return seek(chars, stack - 1, pos + 1)
        elif chars[pos] == lbracket:
            return seek(chars, stack + 1, pos + 1)
        else:
            return seek(chars, stack, pos + 1)

    return seek(chars, 0, pos + 1)


def find_lbracket(ignore, lbracket, rbracket, chars, pos):
    def seek(chars, stack, pos):
        if pos < 0:
            return None
        elif ignore(pos):
            return seek(chars, stack, pos - 1)
        elif chars[pos] == lbracket and stack == 0:
            return pos
        elif chars[pos] == lbracket and stack > 0:
            return seek(chars, stack - 1, pos - 1)
        elif chars[pos] == rbracket:
            return seek(chars, stack + 1, pos - 1)
        else:
            return seek(chars, stack, pos - 1)

    return seek(chars, 0, pos - 1)


def find_nearest_lbracket(ignore, bracket, chars, pos):
    if pos < 0:
        return None
    elif not ignore(pos) and chars[pos] == bracket:
        return pos
    else:
        return find_nearest_lbracket(ignore, bracket, chars, pos - 1)


def find_nearest_rbracket(ignore, bracket, chars, pos):
    if pos >= len(chars):
        return None
    if not ignore(pos) and chars[pos] == bracket:
        return pos
    else:
        return find_nearest_rbracket(ignore, bracket, chars, pos + 1)


def find_any_nearest_lbracket(ignore, chars, pos):
    for bracket in [LPAREN, LBRACKET, LBRACE]:
        match = find_nearest_lbracket(ignore, bracket, chars, pos)
        if match is not None:
            return bracket, match

    return None


def current_form_range(ignore, chars, pos):
    match = find_any_nearest_lbracket(ignore, chars, pos)

    if match is None:
        return None
    else:
        bracket, lpos = match
        rpos = find_rbracket(ignore, bracket, BRACKETS[bracket], chars, pos)
        return lpos, rpos
