from sublime import Region

SEXP_DELIMITERS = "punctuation.section.parens | punctuation.section.brackets | punctuation.section.braces | punctuation.definition.string"
SEXP_BEGIN = "punctuation.section.parens.begin | punctuation.section.brackets.begin | punctuation.section.braces.begin | punctuation.definition.string.begin"
SEXP_END = "punctuation.section.parens.end | punctuation.section.brackets.end | punctuation.section.braces.end | punctuation.definition.string.end"


def inside_string(view, point):
    return view.match_selector(point, "string - punctuation.definition.string.begin")


def inside_comment(view, point):
    return view.match_selector(point, "comment.line")


def ignore(view, point):
    return view.match_selector(
        point,
        "string - punctuation.definition.string.begin | comment.line | constant.character",
    )


def find(view, start_point, selector, forward=True):
    point = start_point if forward else start_point - 1
    max_size = view.size()

    while point >= 0 and point <= max_size:
        if view.match_selector(point, selector):
            return point

        if forward:
            point += 1
        else:
            point -= 1

    return -1


def expand_by_selector(view, start_point, selector):
    point = start_point
    max_point = view.size()
    begin = 0
    end = max_point

    while point > 0:
        if view.match_selector(point, selector) and not view.match_selector(
            point - 1, selector
        ):
            begin = point
            break
        else:
            point -= 1

    while point < max_point:
        if view.match_selector(point - 1, selector) and not view.match_selector(
            point, selector
        ):
            end = point
            break
        else:
            point += 1

    return Region(begin, end)
