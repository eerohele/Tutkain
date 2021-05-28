import re
from sublime import Region

from itertools import groupby
from . import selectors
from . import sexp


def determine_indentation(view, open_bracket):
    end = open_bracket.end()
    line = view.line(end)
    indentation = " " * (end - line.begin())
    region = view.find(r"\S", open_bracket.end())
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


def insert_newline_and_indent(view, edit):
    for region in view.sel():
        point = region.begin()

        if selectors.inside_comment(view, point):
            view.run_command("insert", {"characters": "\n;; "})
        else:
            _, open_bracket = sexp.find_open(view, point)

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


def get_indented_string(view, region, prune=False):
    _, open_bracket = sexp.find_open(view, region.begin())

    string = prune_region(view, region) if prune else view.substr(region)

    if open_bracket:
        indentation = determine_indentation(view, open_bracket)
        return indentation + string.lstrip(" ")
    else:
        return string


IGNORE_SELECTORS = "punctuation.definition.string | string | comment.line"


def indent_region(view, edit, region, prune=False):
    new_lines = []

    if region and not view.match_selector(region.begin(), IGNORE_SELECTORS):
        for line in view.lines(region):
            replacee = line

            if new_lines:
                if previous := new_lines.pop():
                    begin = previous.end()
                    end = begin + line.size()
                    replacee = Region(begin, end)

            if replacer := get_indented_string(view, replacee, prune=prune):
                view.replace(edit, replacee, replacer)
                new_lines.append(view.full_line(replacee.begin()))
