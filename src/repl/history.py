from itertools import groupby

import sublime

MAX_HISTORY_ITEMS = 100
index = None


def get(window):
    global index

    settings = window.settings()

    if settings:
        history = settings.get("repl_history")

        if history and index is not None and index < len(history):
            return history[index]

    return ""


def update(window, code):
    settings = window.settings().to_dict()
    history = settings.get("repl_history")

    if history:
        history.append(code)

        if len(history) > MAX_HISTORY_ITEMS:
            history = history[-MAX_HISTORY_ITEMS:]

        history = [item[0] for item in groupby(history)]
    else:
        history = [code]

    settings["repl_history"] = history
    window.settings().update(settings)


def navigate(view, edit, forward=False):
    global index

    settings = view.window().settings()

    if settings:
        history = settings.get("repl_history")

        if history:
            if index is None:
                # If this is the first time the user requests a history item, set the index to
                # the last history item.
                index = len(history) - 1
            elif not forward and index > 0:
                index -= 1
            elif forward and index < len(history):
                index += 1

    view.erase(edit, sublime.Region(0, view.size()))

    if index is not None and index < len(history):
        view.insert(edit, 0, history[index])
