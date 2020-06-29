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
    else:
        project_data['repl_history'] = [code]

    window.set_project_data(project_data)


class TutkainReplHistoryListener(EventListener):
    def on_deactivated(self, view):
        if view.settings().get('tutkain_repl_input_panel'):
            global index
            index = None


class TutkainNavigateReplHistoryCommand(TextCommand):
    def run(self, edit, forward=False):
        global index

        project_data = self.view.window().project_data()

        if project_data:
            history = project_data.get('repl_history')

            if history:
                if index is None:
                    # If this is the first time the user requests a history item, set the index to
                    # the last history item.
                    index = len(history) - 1
                elif not forward and index > 0:
                    index -= 1
                elif forward and index < len(history):
                    index += 1

        self.view.erase(edit, sublime.Region(0, self.view.size()))

        if index is not None and index < len(history):
            self.view.insert(edit, 0, history[index])
