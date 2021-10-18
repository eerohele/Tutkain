import inspect
from dataclasses import dataclass
from . import selectors
from sublime import CLASS_WORD_START, Region, View


OPEN = {"(": ")", "[": "]", "{": "}"}
CLOSE = {")": "(", "]": "[", "}": "{"}

BEGIN_SELECTORS = inspect.cleandoc("""punctuation.section.parens.begin
| punctuation.section.brackets.begin
| punctuation.section.braces.begin""")

END_SELECTORS = inspect.cleandoc("""punctuation.section.parens.end
| punctuation.section.brackets.end
| punctuation.section.braces.end""")

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

ABSORB_SELECTOR = inspect.cleandoc("""keyword.operator.macro
| punctuation.definition.keyword
| punctuation.definition.comment
| constant.other.keyword""")


@dataclass(eq=True, frozen=True)
class Delimiter:
    selector: str
    region: Region


@dataclass(eq=True, frozen=True)
class Sexp:
    """A dataclass that encapsulates an S-expression in a View.

    Do not initialize directly; use make_sexp instead."""
    view: View
    open: Delimiter
    close: Delimiter

    def __str__(self):
        return self.view.substr(self.extent())

    def extent(self):
        return Region(self.open.region.begin(), self.close.region.end())

    def is_empty(self):
        return self.open.region.end() == self.close.region.begin()

    def contains(self, point):
        return point >= self.open.region.end() and point <= self.close.region.begin()


def absorb_macro_characters(view: View, delimiter: Delimiter):
    """Given a View and a Delimiter that encloses a character that opens an
    S-expression, extend the region to contain all macro characters that
    precede the S-expression, if any."""
    begin = delimiter.region.begin()

    if view.match_selector(begin - 1, ABSORB_SELECTOR):
        # Find the first point that contains a character other than a macro character or a
        # character that's part of a keyword
        boundary = (
            selectors.find(
                view, begin - 1, f"- ({ABSORB_SELECTOR})", forward=False
            )
            + 1
        )

        begin = max(boundary, 0)

    return Delimiter(delimiter.selector, Region(begin, delimiter.region.end()))


def make_sexp(view: View, open_delim: Delimiter, close_delim: Delimiter):
    """Given a View, an open Delimiter, and a close Delimiter, return a Sexp
    instance.

    Use this instead of initializing Sexp directly."""
    return Sexp(view, absorb_macro_characters(view, open_delim), close_delim)


def find_open(view, start_point):
    """Given a View and a start point, find the first point to the left of the
    start point that opens an S-expression, and return a Region that encloses
    that point."""
    point = start_point - 1
    stack = 0

    while point >= 0:
        if stack == 0 and view.match_selector(point, BEGIN_SELECTORS):
            char = view.substr(point)
            region = Region(point, point + 1)
            return Delimiter(CHAR_TO_SELECTOR[char], region)
        elif stack > 0 and view.match_selector(point, BEGIN_SELECTORS):
            stack -= 1
            point -= 1
        elif view.match_selector(point, END_SELECTORS):
            stack += 1
            point -= 1
        else:
            point -= 1

    return None


def find_close(view, open_delim):
    """Given a View and a Region that opens an S-expression, return the Region
    that closes the S-expression."""
    if open_delim is None:
        return None

    point = open_delim.region.end()
    stack = 0
    max_point = view.size()
    end_selector = BEGIN_TO_END_SELECTOR[open_delim.selector]

    while point < max_point:
        if stack == 0 and view.match_selector(point, end_selector):
            region = Region(point, point + 1)
            return Delimiter(end_selector, region)
        elif view.match_selector(point, open_delim.selector):
            stack += 1
            point += 1
        elif stack > 0 and view.match_selector(point, end_selector):
            stack -= 1
            point += 1
        else:
            point += 1


def move_inside(view, point, edge):
    if not edge or selectors.inside_string(view, point):
        return point
    elif (
        (edge is True or edge == "forward") and view.match_selector(point, selectors.SEXP_BEGIN)
    ) or (
        selectors.match_many(view, point, "keyword.operator.macro", selectors.SEXP_BEGIN)) or (
        selectors.match_many(view, point, "keyword.operator.macro", selectors.SEXP_BEGIN)) or (
        selectors.match_many(view, point, "keyword.operator.macro", "keyword.operator.macro", selectors.SEXP_BEGIN)) or (
        selectors.match_many(view, point, "keyword.operator.macro", "keyword.operator.macro", "keyword.operator.macro", selectors.SEXP_BEGIN)) or (
        selectors.match_many(view, point, "punctuation.definition.comment", selectors.SEXP_BEGIN)) or (
        selectors.match_many(view, point, "keyword.operator.macro", "punctuation.definition.comment", selectors.SEXP_BEGIN)
    ):
        return view.find(r"[\(\[\{\"]", point).end()
    elif (edge is True or edge == "backward") and view.match_selector(point - 1, selectors.SEXP_END):
        return point - 1
    else:
        return point


def innermost(view, start_point, edge=True):
    """Given a View and a point, return the innermost S-expression surrounding
    the point.

    If `point` immediately precedes or follows a point whose character opens or
    closes an S-expression, move inside that S-expression before beginning the
    search, unless `edge=False`."""
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
        open_delim = Delimiter("punctuation.definition.string.begin", Region(begin, begin + 1))
        close_delim = Delimiter("punctuation.definition.string.end", Region(end, end + 1))
        return make_sexp(view, open_delim, close_delim)
    else:
        if open_delim := find_open(view, point):
            close_delim = find_close(view, open_delim)
            return make_sexp(view, open_delim, close_delim)


def walk_outward(view, point, edge=True):
    sexp = innermost(view, point, edge=edge)

    while sexp:
        yield sexp
        sexp = innermost(view, sexp.open.region.begin(), edge=False)


def head_word(view, point):
    return view.substr(view.word(view.find_by_class(point, True, CLASS_WORD_START)))


def outermost(view, point, edge=True, ignore={}):
    """Given a View and a point, return the outermost S-expression surrounding
    the point.

    If `point` immediately precedes or follows a point whose character opens or
    closes an S-expression, move inside that S-expression before beginning the
    search, unless `edge=False`.

    If `ignore` is a non-empty set of strings, if the first symbol of the
    outermost S-expression equals one of the strings, ignore that S-expression
    when determining the outermost S-expression and use the previous
    S-expression instead. Useful when ignoring things like Clojure `comment`
    forms, for example."""
    previous = find_open(view, move_inside(view, point, edge))

    while previous and point >= 0:
        if previous.region and view.rowcol(previous.region.begin())[1] == 0:
            return make_sexp(view, previous, find_close(view, previous))

        current = find_open(view, point)

        if previous and (
            not current or (
                ignore and head_word(view, current.region.begin()) in ignore
            )
        ):
            return make_sexp(view, previous, find_close(view, previous))
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
                open_bracket = view.substr(sexp.open.region)
                new_open_bracket = CYCLE_ORDER[open_bracket]

                if new_open_bracket[-1:] in OPEN:
                    new_close_bracket = OPEN[new_open_bracket[-1:]]
                    view.replace(edit, sexp.close.region, new_close_bracket)
                    view.replace(edit, sexp.open.region, new_open_bracket)
