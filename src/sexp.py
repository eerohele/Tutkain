from dataclasses import dataclass
from . import selectors
from sublime import CLASS_WORD_START, Region


OPEN = {"(": ")", "[": "]", "{": "}"}
CLOSE = {")": "(", "]": "[", "}": "{"}

BEGIN_SELECTORS = """punctuation.section.parens.begin
| punctuation.section.brackets.begin
| punctuation.section.braces.begin"""

END_SELECTORS = """punctuation.section.parens.end
| punctuation.section.brackets.end
| punctuation.section.braces.end"""

CHAR_TO_SELECTOR = {
    "(": "punctuation.section.parens.begin",
    "[": "punctuation.section.brackets.begin",
    "{": "punctuation.section.braces.begin"
}

BEGIN_TO_END_SELECTOR = {
    "punctuation.section.parens.begin": "punctuation.section.parens.end",
    "punctuation.section.brackets.begin": "punctuation.section.brackets.end",
    "punctuation.section.braces.begin": "punctuation.section.braces.end"
}


class Sexp:
    absorb_selector = "keyword.operator.macro | punctuation.definition.keyword | punctuation.definition.comment | constant.other.keyword"

    def __init__(self, view, open_region, close_region):
        self.view = view
        self.open = self.absorb_macro_characters(open_region)
        self.close = close_region

    def __str__(self):
        return self.view.substr(self.extent())

    def extent(self):
        return Region(self.open.begin(), self.close.end())

    def is_empty(self):
        return self.open.end() == self.close.begin()

    def contains(self, point):
        return point >= self.open.end() and point <= self.close.begin()

    def absorb_macro_characters(self, region):
        begin = region.begin()

        if self.view.match_selector(begin - 1, self.absorb_selector):
            # Find the first point that contains a character other than a macro character or a
            # character that's part of a keyword
            boundary = (
                selectors.find(
                    self.view, begin - 1, f"- ({self.absorb_selector})", forward=False
                )
                + 1
            )

            begin = max(boundary, 0)

        return Region(begin, region.end())

    def __eq__(self, other):
        return other and self.extent() == other.extent()


@dataclass(eq=True, frozen=True)
class Open:
    selector: str
    region: Region


def find_open(view, start_point):
    point = start_point - 1
    stack = 0

    while point >= 0:
        if stack == 0 and view.match_selector(point, BEGIN_SELECTORS):
            char = view.substr(point)
            region = Region(point, point + 1)
            return Open(CHAR_TO_SELECTOR[char], region)
        elif stack > 0 and view.match_selector(point, BEGIN_SELECTORS):
            stack -= 1
            point -= 1
        elif view.match_selector(point, END_SELECTORS):
            stack += 1
            point -= 1
        else:
            point -= 1

    return None


def find_close(view, opening):
    if opening is None:
        return None

    point = opening.region.end()
    stack = 0
    max_point = view.size()
    end_selector = BEGIN_TO_END_SELECTOR[opening.selector]

    while point < max_point:
        if stack == 0 and view.match_selector(point, end_selector):
            return Region(point, point + 1)
        elif view.match_selector(point, opening.selector):
            stack += 1
            point += 1
        elif stack > 0 and view.match_selector(point, end_selector):
            stack -= 1
            point += 1
        else:
            point += 1


def matches_selector_pattern(view, start_point, patterns):
    point = start_point
    i = 0

    while i < len(patterns):
        if not view.match_selector(point + i, patterns[i]):
            return False

        i += 1

    return True


def has_macro_character_attached_to_sexp(view, point):
    patterns = [
        ["keyword.operator.macro", selectors.SEXP_BEGIN],
        ["punctuation.definition.comment", selectors.SEXP_BEGIN],
        ["keyword.operator.macro", "keyword.operator.macro", selectors.SEXP_BEGIN],
        ["keyword.operator.macro", "punctuation.definition.comment", selectors.SEXP_BEGIN],
        [
            "keyword.operator.macro",
            "keyword.operator.macro",
            "keyword.operator.macro",
            selectors.SEXP_BEGIN,
        ],
    ]

    for pattern in patterns:
        if matches_selector_pattern(view, point, pattern):
            return True

    return False


def move_inside(view, point, edge):
    if not edge or selectors.inside_string(view, point):
        return point
    elif (edge is True or edge == "forward") and view.match_selector(
        point, selectors.SEXP_BEGIN
    ) or has_macro_character_attached_to_sexp(view, point):
        return view.find(r"[\(\[\{\"]", point).end()
    elif (edge is True or edge == "backward") and view.match_selector(point - 1, selectors.SEXP_END):
        return point - 1
    else:
        return point


def innermost(view, start_point, edge=True):
    point = move_inside(view, start_point, edge)

    if selectors.inside_comment(view, point - 1):
        return None
    elif selectors.inside_string(view, point):
        begin = selectors.find(
            view,
            point,
            "punctuation.definition.string.begin - constant.character.escape",
            forward=False,
        )

        end = selectors.find(
            view, point, "punctuation.definition.string.end - constant.character.escape"
        )

        # TODO: Is a string a sexp?
        return Sexp(view, Region(begin, begin + 1), Region(end, end + 1))
    else:
        if punctuation := find_open(view, point):
            close_region = find_close(view, punctuation)
            return Sexp(view, punctuation.region, close_region)


def walk_outward(view, point, edge=True):
    sexp = innermost(view, point, edge=edge)

    while sexp:
        yield sexp
        sexp = innermost(view, sexp.open.begin(), edge=False)


def head_word(view, point):
    return view.substr(view.word(view.find_by_class(point, True, CLASS_WORD_START)))


def make_sexp(view, begin):
    close_region = find_close(view, begin)
    return Sexp(view, begin.region, close_region)


def outermost(view, point, edge=True, ignore={}):
    previous = find_open(view, move_inside(view, point, edge))

    while previous and point >= 0:
        current = find_open(view, point)

        if previous and (
            not current or (
                ignore and head_word(view, current.region.begin()) in ignore
            )
        ):
            return make_sexp(view, previous)
        else:
            point = previous.region.begin()
            previous = current


CYCLE_ORDER = {"(": "[", "[": "{", "{": "#{", "#{": "("}


def cycle_collection_type(view, edit):
    for region in view.sel():
        point = region.begin()

        if not selectors.ignore(view, point):
            if view.match_selector(point, "string") or view.match_selector(
                point - 1, "string"
            ):
                edge = False
            else:
                edge = True

            sexp = innermost(view, point, edge=edge)

            if sexp:
                open_bracket = view.substr(sexp.open)
                new_open_bracket = CYCLE_ORDER[open_bracket]

                if new_open_bracket[-1:] in OPEN:
                    new_close_bracket = OPEN[new_open_bracket[-1:]]
                    view.replace(edit, sexp.close, new_close_bracket)
                    view.replace(edit, sexp.open, new_open_bracket)
