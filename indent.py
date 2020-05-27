import re
import sublime

from . import sexp


def symbol_in_head_position(view, open_bracket):
    point = view.find_by_class(
        open_bracket.begin(),
        True,
        sublime.CLASS_WORD_START
    )

    # This is probably not 100% correct. Also, it is tied to the syntax
    # definition. Is that a problem?
    return view.match_selector(point, 'variable | storage')


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
        _, open_bracket = sexp.find_open_bracket(view, point)

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


def get_indented_string(view, region):
    _, open_bracket = sexp.find_open_bracket(view, region.begin())

    if open_bracket:
        indentation = determine_indentation(view, open_bracket)
        return indentation + view.substr(region).lstrip(' ')


def indent_region(view, edit, region):
    new_lines = []

    for line in view.lines(region):
        replacee = line

        if new_lines:
            previous = new_lines.pop()
            if previous:
                begin = previous.end()
                end = begin + line.size()
                replacee = sublime.Region(begin, end)

        replacer = get_indented_string(view, replacee)

        if replacer:
            view.replace(edit, replacee, replacer)
            new_lines.append(view.full_line(replacee.begin()))
