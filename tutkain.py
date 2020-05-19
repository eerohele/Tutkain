import sublime
import sublime_plugin
from threading import Thread

from . import brackets
from . import formatter
from .log import enable_debug, log
from .repl import ClientRegistry, Client


def plugin_loaded():
    settings = sublime.load_settings('{}.sublime-settings'.format('tutkain'))

    if settings.get('debug', False):
        enable_debug()


def plugin_unloaded():
    for id in ClientRegistry.get_all():
        log.debug({'event': 'client/halt', 'id': 'id'})
        ClientRegistry.get(id).halt()

    ClientRegistry.deregister_all()


def print_characters(panel, characters):
    if characters is not None:
        panel.run_command('append', {
            'characters': characters,
            'scroll_to_end': True
        })


def append_to_output_panel(window, message):
    if message:
        panel = window.find_output_panel('tutkain')

        window.run_command('show_panel', {'panel': 'output.tutkain'})

        panel.set_read_only(False)
        print_characters(panel, formatter.format(message))
        panel.set_read_only(True)

        panel.run_command('move_to', {'to': 'eof'})


def region_content(view):
    return view.substr(sublime.Region(0, view.size()))


class TutkainClearOutputPanelCommand(sublime_plugin.WindowCommand):
    def run(self):
        panel = self.window.find_output_panel('tutkain')
        panel.set_read_only(False)
        panel.run_command('select_all')
        panel.run_command('right_delete')
        panel.set_read_only(True)


class TutkainEvaluateFormCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        client = ClientRegistry.get(window.id())

        if client is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            for region in self.view.sel():
                eval_region = region if not region.empty() else (
                    brackets.current_form_region(
                        self.view,
                        region.begin()
                    )
                )

                code = self.view.substr(eval_region)

                client.output.put({'out': '=> {}\n'.format(code)})

                log.debug({
                    'event': 'send',
                    'scope': 'form',
                    'code': code
                })

                client.eval(
                    code,
                    handler=lambda response: (
                        client.output.put({'append': '\n'})
                        if response.get('status') == ['done']
                        else client.output.put(response)
                    )
                )


class TutkainEvaluateViewCommand(sublime_plugin.TextCommand):
    def handler(self, client, response):
        if response.get('status') == ['done']:
            client.output.put({'append': '\n'})
        elif response.get('value'):
            pass
        else:
            client.output.put(response)

    def run(self, edit):
        window = self.view.window()
        client = ClientRegistry.get(window.id())

        if client is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            client.output.put({'out': 'Loading view...'})

            client.eval(
                region_content(self.view),
                handler=lambda response: self.handler(client, response)
            )


class TutkainRunTestsInCurrentNamespaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        window = self.view.window()
        client = ClientRegistry.get(window.id())

        if client is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            client.eval(
                region_content(self.view),
                owner='plugin',
                handler=lambda response: (
                    response.get('status') == ['done'] and
                    client.eval(
                        '''
                        ((requiring-resolve 'clojure.test/run-tests))
                        ''',
                        owner='plugin'
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
        panel = 'output.tutkain'

        if active_panel == panel:
            self.window.run_command('hide_panel', {'panel': panel})
        else:
            self.window.run_command('show_panel', {'panel': panel})


class TutkainEvaluateInputCommand(sublime_plugin.WindowCommand):
    def eval(self, code):
        client = ClientRegistry.get(self.window.id())

        if client is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            client.output.put({'out': '=> {}\n'.format(code)})

            client.eval(
                code,
                handler=lambda response: (
                    client.output.put({'append': '\n'})
                    if response.get('status') == ['done']
                    else client.output.put(response)
                )
            )

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
        panel = self.window.find_output_panel('tutkain')
        if panel is None:
            panel = self.window.create_output_panel('tutkain')

        panel.set_name('tutkain')
        panel.settings().set('line_numbers', False)
        panel.settings().set('gutter', False)
        panel.settings().set('is_widget', True)
        panel.settings().set('scroll_past_end', False)
        panel.set_read_only(True)
        panel.assign_syntax('Packages/Clojure/Clojure.sublime-syntax')

    def print_loop(self, client):
        while True:
            item = client.output.get()

            if item is None:
                break

            log.debug({'event': 'printer/recv', 'data': item})

            append_to_output_panel(self.window, item)

        log.debug({'event': 'thread/exit'})

    def run(self, host, port):
        try:
            client = Client(host, int(port))
            ClientRegistry.register(self.window.id(), client)

            client.go()
            client.describe()

            # Start a worker that reads values from a Client output queue
            # and prints them into an output panel.
            print_loop = Thread(
                daemon=True,
                target=self.print_loop,
                args=(client,)
            )
            print_loop.name = 'tutkain.print_loop'
            print_loop.start()

            # Create an output panel for printing evaluation results and show
            # it.
            self.configure_output_panel()
        except ConnectionRefusedError:
            self.window.status_message(
                'ERR: connection to {}:{} refused.'.format(host, port)
            )

    def input(self, args):
        return HostInputHandler(self.window)


class TutkainDisconnectCommand(sublime_plugin.WindowCommand):
    def run(self):
        client = ClientRegistry.get(self.window.id())

        if client is not None:
            client.output.put({'out': 'Disconnecting...'})
            client.halt()
            client = None
            ClientRegistry.deregister(self.window.id())
            self.window.status_message('REPL disconnected.')


class TutkainNewScratchView(sublime_plugin.WindowCommand):
    def run(self):
        view = self.window.new_file()
        view.set_name('*scratch*')
        view.set_scratch(True)
        view.assign_syntax('Packages/Clojure/Clojure.sublime-syntax')
        self.window.focus_view(view)


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


class TutkainInterruptEvaluationCommand(sublime_plugin.WindowCommand):
    def run(self):
        client = ClientRegistry.get(self.window.id())

        if client is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            session_id = client.sessions_by_owner['user'].id
            log.debug({'event': 'eval/interrupt', 'id': session_id})
            client.input.put({'op': 'interrupt', 'session': session_id})
