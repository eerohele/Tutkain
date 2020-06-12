import re
import sublime

from itertools import groupby
from operator import itemgetter
from . import sexp


def symbol_in_head_position(view, open_bracket):
    region = view.find(r'\S', open_bracket.end())

    # This is probably not 100% correct. Also, it is tied to the syntax
    # definition. Is that a problem?
    return view.match_selector(region.begin(), 'variable | storage')


def determine_indentation(view, open_bracket):
    end = open_bracket.end()
    line = view.line(end)
    indentation = ' ' * (end - line.begin())

    if symbol_in_head_position(view, open_bracket):
        return indentation + ' '
    else:
        return indentation


def restore_cursors(view):
    # I have no idea why I need to do this, but if I don't, after this
    # command has finished executing, the view will be in a state where
    # the indentation we just added is selected.
    ends = [region.end() for region in view.sel()]
    view.sel().clear()

    for end in ends:
        view.sel().add(sublime.Region(end, end))


def insert_newline_and_indent(view, edit):
    for region in view.sel():
        point = region.begin()

        if sexp.inside_comment(view, point):
            view.run_command('insert', {'characters': '\n;; '})
        else:
            _, open_bracket = sexp.find_open(view, point)

            if open_bracket is None:
                view.run_command('insert', {'characters': '\n'})
            else:
                end = region.end()
                view.insert(edit, end, '\n')
                point_after_newline = end + 1
                line = view.line(point_after_newline)
                indentation = determine_indentation(view, open_bracket)
                new_line = indentation + view.substr(line).lstrip()
                view.replace(edit, line, new_line)
                restore_cursors(view)


def prune_string(string):
    '''Prune a string.

    - Replace multiple consecutive spaces with a single space.
    - Remove spaces after open brackets.
    - Remove spaces before close brackets.
    '''
    return re.sub(
        r' +(?=[\)\]\}])', '', re.sub(r'(?<=[\(\[\{]) +', '', re.sub(r'  +', ' ', string))
    )


def fuse(lst):
    '''Given a list of points, fuse any consecutive runs of points into regions.'''
    ranges = []

    # https://docs.python.org/2.6/library/itertools.html#examples
    for k, g in groupby(enumerate(lst), lambda x: x[0] - x[1]):
        group = list(map(itemgetter(1), g))
        ranges.append(sublime.Region(group[0], group[-1]))

    return ranges


def non_ignored_regions(view, region):
    '''Given a region, return a list of the regions within that region that do not constitute an
    ignored region (a string or a comment).'''
    points = []
    point = region.begin()

    while point <= region.end():
        if not sexp.ignore(view, point) and not re.match(r'[\n\x00]', view.substr(point)):
            points.append(point)

        point += 1

    regions = fuse(points)

    if regions:
        regions.append(sublime.Region(region.end(), region.end()))

    return regions


def pairwise(lst):
    for index in range(len(lst)):
        next_index = index + 1

        if next_index >= len(lst):
            yield lst[index], None
        else:
            yield lst[index], lst[next_index]


def prune_region(view, region):
    '''Prune extraneous whitespace in the given region.'''
    strings = []
    regions = non_ignored_regions(view, region)

    if regions:
        for a, b in pairwise(regions):
            if b is not None:
                strings.append(prune_string(view.substr(a)))
                strings.append(view.substr(sublime.Region(a.end(), b.begin())))
                strings.append(prune_string(view.substr(b)))

    return ''.join(strings)


def get_indented_string(view, region, prune=False):
    _, open_bracket = sexp.find_open(view, region.begin())

    if prune:
        string = prune_region(view, region)
    else:
        string = view.substr(region)

    if open_bracket:
        indentation = determine_indentation(view, open_bracket)
        return indentation + string.lstrip(' ')
    else:
        return string


IGNORE_SELECTORS = 'punctuation.definition.string | string | comment'


def indent_region(view, edit, region, prune=False):
    new_lines = []

    if region and not view.match_selector(region.begin(), IGNORE_SELECTORS):
        for line in view.lines(region):
            replacee = line

            if new_lines:
                previous = new_lines.pop()
                if previous:
                    begin = previous.end()
                    end = begin + line.size()
                    replacee = sublime.Region(begin, end)

            replacer = get_indented_string(view, replacee, prune=prune)

            if replacer:
                view.replace(edit, replacee, replacer)
                new_lines.append(view.full_line(replacee.begin()))
