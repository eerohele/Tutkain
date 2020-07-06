from itertools import groupby

import sublime
from sublime_plugin import EventListener, TextCommand


index = None


def get(window):
    global index

    project_data = window.project_data()

    if project_data:
        history = project_data.get('repl_history')

        if history and index is not None and index < len(history):
            return history[index]

    return ''


MAX_HISTORY_ITEMS = 100


def update(window, code):
    project_data = window.project_data() or {}
    history = project_data.get('repl_history')

    if history:
        history.append(code)

        if len(history) > MAX_HISTORY_ITEMS:
            project_data['repl_history'] = history[-MAX_HISTORY_ITEMS:]

        project_data['repl_history'] = [item[0] for item in groupby(history)]
    else:
        project_data['repl_history'] = [code]

    window.set_project_data(project_data)
