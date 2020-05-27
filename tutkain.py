import os
import sublime
import sublime_plugin
from threading import Thread

from . import sexp
from . import formatter
from . import indent
from . import sessions
from .log import enable_debug, log
from .repl import Client


def plugin_loaded():
    settings = sublime.load_settings('{}.sublime-settings'.format('tutkain'))

    if settings.get('debug', False):
        enable_debug()


def plugin_unloaded():
    sessions.wipe()


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
        session = sessions.get_by_owner(window.id(), 'user')

        if session is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            for region in self.view.sel():
                eval_region = region if not region.empty() else (
                    sexp.outermost(
                        self.view,
                        sexp.into_adjacent(self.view, region.begin()),
                        absorb=True,
                        ignore={'comment'}
                    )
                )

                code = self.view.substr(eval_region)

                session.output({'out': '=> {}\n'.format(code)})

                log.debug({
                    'event': 'send',
                    'scope': 'form',
                    'code': code
                })

                session.send(
                    {'op': 'eval',
                     'code': code,
                     'file': self.view.file_name()},
                    handler=lambda response: (
                        session.output({'append': '\n'})
                        if response.get('status') == ['done']
                        else session.output(response)
                    )
                )


class TutkainEvaluateViewCommand(sublime_plugin.TextCommand):
    def handler(self, session, response):
        if response.get('value'):
            pass
        else:
            session.output(response)

    def run(self, edit):
        window = self.view.window()
        session = sessions.get_by_owner(window.id(), 'user')

        if session is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            session.output({'out': 'Loading view...\n'})

            session.send(
                {'op': 'eval',
                 'code': region_content(self.view),
                 'file': self.view.file_name()},
                handler=lambda response: self.handler(session, response)
            )


class TutkainRunTestsInCurrentNamespaceCommand(sublime_plugin.TextCommand):
    def evaluate_view(self, session, response):
        if response.get('status') == ['done']:
            session.send(
                {'op': 'eval',
                 'code': region_content(self.view),
                 'file': self.view.file_name()},
                handler=lambda response: self.run_tests(session, response)
            )

    def run_tests(self, session, response):
        if response.get('status') == ['eval-error']:
            session.denounce(response)
        elif response.get('status') == ['done']:
            if not session.is_denounced(response):
                session.send(
                    {'op': 'eval',
                     'code': '((requiring-resolve \'clojure.test/run-tests))',
                     'file': self.view.file_name()},
                    handler=lambda response: (
                        session.output({'append': '\n'})
                        if response.get('status') == ['done']
                        else session.output(response)
                    )
                )
        elif response.get('value'):
            pass
        else:
            session.output(response)

    def run(self, edit):
        window = self.view.window()
        session = sessions.get_by_owner(window.id(), 'plugin')

        if session is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            session.send(
                {'op': 'eval',
                 'code': '''
                         (run! (fn [[sym _]] (ns-unmap *ns* sym))
                               (ns-publics *ns*))
                         ''',
                 'file': self.view.file_name()},
                handler=lambda response: self.evaluate_view(session, response)
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

    def read_port(self, path):
        with open(path, 'r') as file:
            return (path, file.read())

    def discover_ports(self):
        # I mean, this is Pythonic, right...?
        return list(
            map(
                self.read_port,
                filter(
                    os.path.isfile,
                    map(
                        lambda folder: os.path.join(folder, '.nrepl-port'),
                        self.window.folders()
                    )
                )
            )
        )

    def next_input(self, host):
        ports = self.discover_ports()

        if len(ports) > 1:
            return PortsInputHandler(ports)
        elif len(ports) == 1:
            return PortInputHandler(ports[0][1])
        else:
            return PortInputHandler('')


class PortInputHandler(sublime_plugin.TextInputHandler):
    def __init__(self, default_value):
        self.default_value = default_value

    def name(self):
        return 'port'

    def placeholder(self):
        return 'Port'

    def validate(self, text):
        return text.isdigit()

    def initial_text(self):
        return self.default_value


class PortsInputHandler(sublime_plugin.ListInputHandler):
    def __init__(self, ports):
        self.ports = ports

    def name(self):
        return 'port'

    def validate(self, text):
        return text.isdigit()

    def contract_path(self, path):
        return path.replace(os.path.expanduser('~'), '~')

    def list_items(self):
        return list(
            map(
                lambda x: (
                    '{} ({})'.format(x[1], self.contract_path(x[0])), x[1]
                ),
                self.ports
            )
        )


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
        session = sessions.get_by_owner(self.window.id(), 'user')

        if session is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            session.output({'out': '=> {}\n'.format(code)})

            session.send(
                {'op': 'eval', 'code': code},
                handler=lambda response: (
                    session.output({'append': '\n'})
                    if response.get('status') == ['done']
                    else session.output(response)
                )
            )

    def noop(*args):
        pass

    def run(self):
        view = self.window.show_input_panel(
            'Input: ',
            '',
            self.eval,
            self.noop,
            self.noop
        )

        view.assign_syntax('Clojure.sublime-syntax')


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

    def print_loop(self, recvq):
        while True:
            item = recvq.get()

            if item is None:
                break

            log.debug({'event': 'printer/recv', 'data': item})

            append_to_output_panel(self.window, item)

        log.debug({'event': 'thread/exit'})

    def run(self, host, port):
        window = self.window

        try:
            client = Client(host, int(port)).go()

            plugin_session = client.clone_session()
            sessions.register(window.id(), 'plugin', plugin_session)

            user_session = client.clone_session()
            sessions.register(window.id(), 'user', user_session)

            # Create an output panel for printing evaluation results and show
            # it.
            self.configure_output_panel()

            # Start a worker thread that reads items from a queue and prints
            # them into an output panel.
            print_loop = Thread(
                daemon=True,
                target=self.print_loop,
                args=(client.recvq,)
            )
            print_loop.name = 'tutkain.print_loop'
            print_loop.start()

            plugin_session.output(
                {'out': 'Connected to {}:{}.\n'.format(host, port)}
            )

            plugin_session.client.sendq.put({'op': 'describe'})
        except ConnectionRefusedError:
            window.status_message(
                'ERR: connection to {}:{} refused.'.format(host, port)
            )

    def input(self, args):
        return HostInputHandler(self.window)


class TutkainDisconnectCommand(sublime_plugin.WindowCommand):
    def run(self):
        window = self.window
        session = sessions.get_by_owner(window.id(), 'plugin')

        if session is not None:
            session.output({'out': 'Disconnecting...\n'})
            session.terminate()
            user_session = sessions.get_by_owner(window.id(), 'user')
            user_session.terminate()
            sessions.deregister(window.id())
            window.status_message('REPL disconnected.')


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
            return 'Clojure' in syntax


class TutkainExpandSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        selection = view.sel()

        # TODO: Add proper support for multiple cursors.
        for region in selection:
            point = region.begin()

            if not region.empty():
                view.run_command('expand_selection', {'to': 'scope'})
            else:
                # If we're next to a character that delimits a Clojure form
                if sexp.is_next_to_expand_anchor(view, point):
                    start_point = sexp.into_adjacent(view, region.begin())

                    selection.add(
                        sexp.innermost(view, start_point, absorb=True)
                    )
                # If the next character is a double quote
                elif view.substr(point) == '"':
                    # Move cursor to within string
                    selection.add(sublime.Region(point + 1))

                    # Then expand
                    view.run_command('expand_selection', {'to': 'scope'})
                else:
                    view.run_command('expand_selection', {'to': 'scope'})


class TutkainInterruptEvaluationCommand(sublime_plugin.WindowCommand):
    def run(self):
        session = sessions.get_by_owner(self.window.id(), 'user')

        if session is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            log.debug({'event': 'eval/interrupt', 'id': session.id})
            session.send({'op': 'interrupt'})


class TutkainInsertNewline(sublime_plugin.TextCommand):
    def run(self, edit):
        if 'Clojure' in self.view.settings().get('syntax'):
            indent.insert_newline_and_indent(self.view, edit)


class TutkainIndentRegion(sublime_plugin.TextCommand):
    def run(self, edit):
        if 'Clojure' in self.view.settings().get('syntax'):
            for region in self.view.sel():
                if region.empty():
                    outermost = sexp.outermost(self.view, region.begin())
                    indent.indent_region(self.view, edit, outermost)
                else:
                    indent.indent_region(self.view, edit, region)
