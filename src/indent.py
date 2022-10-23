import math
import re
import textwrap
from sublime import Region

from itertools import groupby
from . import selectors
from . import sexp


def determine_indentation(view, open_bracket):
    end = open_bracket.region.end()
    line = view.line(end)
    indentation = " " * (end - line.begin())
    region = view.find(r"\S", open_bracket.region.end())
    point = region.begin()

    if view.match_selector(point, "meta.special-form | variable | keyword.declaration | keyword.control | storage.type | entity.name"):
        return indentation + " "
    elif view.match_selector(point, "meta.statement.require | meta.statement.import"):
        form = selectors.expand_by_selector(view, point, "meta.statement.require | meta.statement.import")
        first_require = selectors.find(view, form.end(), "punctuation | meta.reader-form")

        if line.contains(first_require):
            return indentation + (" " * (form.size() + 1))
        else:
            return indentation
    else:
        return indentation


def restore_cursors(view):
    # I have no idea why I need to do this, but if I don't, after this
    # command has finished executing, the view will be in a state where
    # the indentation we just added is selected.
    ends = [region.end() for region in view.sel()]
    view.sel().clear()

    for end in ends:
        view.sel().add(Region(end, end))


def insert_newline_and_indent(view, edit, extend_comment=True):
    for region in view.sel():
        point = region.begin()

        if extend_comment and selectors.inside_comment(view, point):
            view.run_command("insert", {"characters": "\n;; "})
        else:
            open_bracket = sexp.find_open(view, point)

            if open_bracket is None:
                view.insert(edit, point, "\n")
            else:
                end = region.end()
                view.insert(edit, end, "\n")
                point_after_newline = end + 1
                line = view.line(point_after_newline)
                indentation = determine_indentation(view, open_bracket)
                new_line = indentation + view.substr(line).lstrip()
                view.replace(edit, line, new_line)
                restore_cursors(view)


def prune_string(string):
    """Prune a string.

    - Replace multiple consecutive spaces with a single space.
    - Remove spaces after open brackets.
    - Remove spaces before close brackets.
    """
    return re.sub(
        r" +(?=[\)\]\}])",
        "",
        re.sub(r"(?<=[\(\[\{]) +", "", re.sub(r"  +", " ", string)),
    )


def fuse(lst):
    ranges = []

    # https://docs.python.org/2.6/library/itertools.html#examples
    for prune, g in groupby(lst, lambda x: x[0]):
        # Err...
        group = list(g)

        # Ehhh... sorry.
        begin = group[0][1][0]
        end = group[-1][1][1]

        ranges.append((prune, Region(begin, end)))

    return ranges


def classify_region(view, region):
    """Given a region, return a list of pairs where the first item of the pair indicates whether
    the region in the other item should be pruned."""
    points = []
    point = region.begin()
    end = region.end()

    while point <= end:
        prune = not view.match_selector(point, "string | comment")
        points.append((prune, (point, min(point + 1, end))))
        point += 1

    return fuse(points)


def prune_region(view, region):
    """Prune extraneous whitespace in the given region."""
    strings = []
    regions = classify_region(view, region)

    for prune, region in regions:
        string = view.substr(region)
        strings.append(prune_string(string) if prune else string)

    return "".join(strings)


def get_indented_string(view, open_bracket, region, prune=False):
    string = prune_region(view, region) if prune else view.substr(region)

    if view.match_selector(region.begin(), "string"):
        return view.substr(region)
    if open_bracket:
        indentation = determine_indentation(view, open_bracket)
        return indentation + string.lstrip(" ")
    else:
        return string


IGNORE_SELECTORS = "punctuation.definition.string | string | comment.line"


def indent_region(view, edit, region, prune=False):
    if region and not view.match_selector(region.begin(), IGNORE_SELECTORS):
        new_lines = []

        for line in view.lines(region):
            replacee = line

            if new_lines:
                if previous := new_lines.pop():
                    begin = previous.end()
                    end = begin + line.size()
                    replacee = Region(begin, end)

            open_bracket = sexp.find_open(view, replacee.begin())
            if replacer := get_indented_string(view, open_bracket, replacee, prune=prune):
                view.replace(edit, replacee, replacer)
                new_lines.append(view.full_line(replacee.begin()))
                restore_cursors(view)


def reindent(code, column):
    # TODO: Clean this up
    lines = code.splitlines()
    new_lines = []

    for line in lines[1:]:
        chars = []
        seen_significant_char = False

        for index, char in enumerate(line):
            if char != " ":
                seen_significant_char = True

            if not seen_significant_char and index < column:
                pass
            else:
                chars.append(char)

        new_lines.append("".join(chars))

    return (lines[0] + "\n" + "\n".join(new_lines)).strip()


def normalize_whitespace(string):
    return " ".join(string.split())


def wrap_text(text, width, indent):
    return textwrap.wrap(text, width=width - len(indent), subsequent_indent=indent)


def leading_spaces(view, start_point):
    point = view.line(start_point).begin()
    spaces = 0

    while view.substr(point).isspace():
        spaces += 1
        point += 1

    return spaces * " "


def hard_wrap_string(view, edit, region, width):
    point = region.begin()

    if region.empty():
        region = selectors.expand_by_selector(view, point, 'string')

    indent = leading_spaces(view, region.begin())

    text = view.substr(region)
    text = re.sub(r"\n(\s)+\n", "\n\n", text)

    paragraphs = map(
        lambda string: "\n".join(string),
        [wrap_text(normalize_whitespace(paragraph), width, indent)
        for paragraph in text.split("\n\n")]
    )

    view.replace(edit, region, f"\n\n{indent}".join(paragraphs))


def hard_wrap_comment(view, edit, region, width):
    point = region.begin()
    indent = leading_spaces(view, view.line(point).begin())

    if region.empty():
        current_line = line = view.line(point)

        # Seek the line where the comment begins.
        while (point := line.begin() - 1) and view.substr(point) != "\x00" and view.match_selector(line.end(), 'comment'):
            line = view.line(point)

        # The beginning of the line is the beginning of the view, and the
        # line has a comment.
        if view.substr(line.begin() - 1) == "\x00" and view.match_selector(line.end(), 'comment'):
            # Find the first point on the line with a non-comment character
            # if exists, else the beginning of the line.
            non_comment_point = selectors.find(view, line.begin(), 'meta.reader-form')

            if non_comment_point is not None:
                begin = non_comment_point + 1
            else:
                begin = line.begin()
        else:
            begin = line.end() + 1

        line = current_line

        while (point := line.end()) and view.substr(point) != "\x00" and view.match_selector(point, 'comment'):
            line = view.line(point + 1)

        if view.substr(line.end()) == "\x00":
            end = line.end()
        else:
            end = line.begin() - 1

        region = Region(begin, end)

    new_lines = []

    text = ''.join(
        map(
            lambda pair: view.substr(pair[0]),
            filter(lambda pair: view.match_selector(pair[0].begin(), '-punctuation'),
                view.extract_tokens_with_scopes(region)
            )
        )
    )

    text = re.sub(r"\n(\s)+\n", "\n\n", text)
    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        paragraph = " ".join(paragraph.split())
        new_paragraphs = textwrap.wrap(paragraph, width=width - 4 - len(indent), subsequent_indent=indent)
        new_paragraphs = map(lambda paragraph: paragraph.lstrip(), new_paragraphs)
        new_line = f"{indent};; " + (f"\n{indent};; ".join(new_paragraphs))
        new_lines.append(new_line)

    view.replace(edit, region, f"\n{indent};;\n".join(new_lines))


# TODO: Don't break if the first non-whitespace char is a hyphen
def hard_wrap(view, edit, width):
    for region in view.sel():
        if view.match_selector(region.begin(), 'string'):
            hard_wrap_string(view, edit, region, width)
        elif view.match_selector(region.begin(), 'comment'):
            hard_wrap_comment(view, edit, region, width)
