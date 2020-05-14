import sublime
import sublime_plugin
from threading import Thread

from . import brackets
from . import formatter
from .log import enable_debug, log
from . import repl_client


def plugin_loaded():
    settings = sublime.load_settings('{}.sublime-settings'.format('tutkain'))

    if settings.get('debug', False):
        enable_debug()


def plugin_unloaded():
    for id in repl_client.get_all():
        log.debug({'event': 'repl/halt', 'id': 'id'})
        repl_client.get(id).halt()

    repl_client.deregister_all()


def print_characters(panel, characters):
    if characters is not None:
        panel.run_command('append', {
            'characters': characters,
            'scroll_to_end': True
        })


def append_to_output_panel(window, message, ensure=False):
    if message:
        panel = window.find_output_panel('panel')

        if ensure:
            window.run_command('show_panel', {'panel': 'output.panel'})

        panel.set_read_only(False)
        print_characters(panel, formatter.format(message))
        panel.set_read_only(True)

        panel.run_command('move_to', {'to': 'eof'})


def region_content(view):
    return view.substr(sublime.Region(0, view.size()))


class TutkainClearOutputPanelCommand(sublime_plugin.WindowCommand):
    def run(self):
        panel = self.window.find_output_panel('panel')
        panel.set_read_only(False)
        panel.run_command('select_all')
        panel.run_command('right_delete')
        panel.set_read_only(True)


class TutkainEvaluateFormCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        repl = repl_client.get(window.id())

        if repl is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            for region in self.view.sel():
                eval_region = region

                if eval_region.empty():
                    eval_region = brackets.current_form_region(
                        self.view,
                        region.begin()
                    )

                if eval_region:
                    code = self.view.substr(eval_region)
                    append_to_output_panel(window, {'in': code}, ensure=True)

                    log.debug({
                        'event': 'send',
                        'scope': 'form',
                        'code': code
                    })

                    repl.eval(code)


class TutkainEvaluateViewCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        repl = repl_client.get(window.id())

        if repl is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            append_to_output_panel(
                window,
                {'append': ';; Loading view...'},
                ensure=True
            )

            repl.eval(
                region_content(self.view),
                session_key='plugin',
                handler=lambda item: (
                    item.get('status') == ['done'] and
                    append_to_output_panel(
                        self.view.window(),
                        {'append': 'loaded.\n'}
                    )
                )
            )


class TutkainRunTestsInCurrentNamespaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        repl = repl_client.get(window.id())

        if repl is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            repl.eval(
                region_content(self.view),
                session_key='plugin',
                handler=lambda item: (
                    item.get('status') == ['done'] and
                    repl.eval(
                        '''
                        ((requiring-resolve 'clojure.test/run-tests))
                        ''',
                        session_key='plugin'
                    )
                )
            )


class HostInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, window):
        self.window = window

    def placeholder(self):
        return 'Host'

    def validate(self, text):
        return len(text) > 0

    def initial_text(self):
        return 'localhost'

    def next_input(self, host):
        return PortInputHandler(self.window)


class PortInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, window):
        self.window = window

    def placeholder(self):
        return 'Port'

    def validate(self, text):
        return text.isdigit()


class TutkainToggleOutputPanelCommand(sublime_plugin.WindowCommand):
    def run(self):
        active_panel = self.window.active_panel()
        panel = 'output.panel'

        if active_panel == panel:
            self.window.run_command('hide_panel', {'panel': panel})
        else:
            self.window.run_command('show_panel', {'panel': panel})


class TutkainEvaluateInputCommand(sublime_plugin.WindowCommand):
    def eval(self, code):
        repl = repl_client.get(self.window.id())

        if repl is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            append_to_output_panel(self.window, {'in': code}, ensure=True)

            repl.eval(code)

    def noop(*args):
        pass

    def run(self):
        self.window.show_input_panel(
            'Input: ',
            '',
            self.eval,
            self.noop,
            self.noop
        )


class TutkainConnectCommand(sublime_plugin.WindowCommand):
    def configure_output_panel(self):
        panel = self.window.find_output_panel('panel')
        if panel is None:
            panel = self.window.create_output_panel('panel')

        panel.set_name('panel')
        panel.settings().set('line_numbers', False)
        panel.settings().set('gutter', False)
        panel.settings().set('is_widget', True)
        panel.settings().set('scroll_past_end', False)
        panel.set_read_only(True)
        panel.assign_syntax('Packages/Clojure/Clojure.sublime-syntax')

    def print_loop(self, repl):
        while True:
            item = repl.output.get()

            if item is None:
                break

            log.debug({'event': 'printer/recv', 'data': item})

            versions = item.get('versions')

            if versions:
                clojure_version = versions.get('clojure').get('version-string')
                nrepl_version = versions.get('nrepl').get('version-string')

                append_to_output_panel(
                    self.window,
                    {'out': 'Clojure {}'.format(clojure_version)}
                )

                append_to_output_panel(
                    self.window,
                    {'out': 'nREPL {}'.format(nrepl_version)}
                )

            append_to_output_panel(self.window, item)

        log.debug({'event': 'thread/exit'})

    def run(self, host, port):
        try:
            repl = repl_client.ReplClient(host, int(port))
            repl_client.register(self.window.id(), repl)

            repl.go()
            repl.describe()

            # Start a worker that reads values from a ReplClient output queue
            # and prints them into an output panel.
            print_loop = Thread(
                daemon=True,
                target=self.print_loop,
                args=(repl,)
            )
            print_loop.name = 'tutkain.print_loop'
            print_loop.start()

            # Create an output panel for printing evaluation results and show
            # it.
            self.configure_output_panel()

            message = 'Connected to {}:{}.'.format(host, port)
            append_to_output_panel(self.window, {'out': message}, ensure=True)
        except ConnectionRefusedError:
            self.window.status_message(
                'ERR: connection to {}:{} refused.'.format(host, port)
            )

    def input(self, args):
        return HostInputHandler(self.window)


class TutkainDisconnectCommand(sublime_plugin.WindowCommand):
    def run(self):
        repl = repl_client.get(self.window.id())

        if repl is not None:
            repl.halt()
            repl = None
            repl_client.deregister(self.window.id())

            append_to_output_panel(self.window, {'out': 'Disconnected.'})


class TutkainListenerCommand(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == 'tutkain.should':
            syntax = view.settings().get('syntax')
            return 'Clojure' in syntax or 'Markdown' in syntax


class TutkainExpandSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        selection = view.sel()

        # TODO: Add proper support for multiple cursors.
        for region in selection:
            pos = region.begin()

            if not region.empty():
                view.run_command('expand_selection', {'to': 'scope'})
            else:
                # If we're next to a character that delimits a Clojure form
                if brackets.is_next_to_expand_anchor(view, pos):
                    selection.add(brackets.current_form_region(view, pos))
                # If the next character is a double quote
                elif brackets.char_range(view, pos, pos + 1) == '"':
                    # Move cursor to within string
                    selection.add(sublime.Region(pos + 1))

                    # Then expand
                    view.run_command('expand_selection', {'to': 'scope'})
                else:
                    view.run_command('expand_selection', {'to': 'scope'})
