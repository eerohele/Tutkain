import os
import sublime

from sublime_plugin import (
    EventListener,
    ListInputHandler,
    TextCommand,
    TextInputHandler,
    ViewEventListener,
    WindowCommand
)

from threading import Thread

from . import sexp
from . import formatter
from . import indent
from . import sessions
from . import paredit
from . import namespace
from .log import enable_debug, log
from .repl import Client


view_registry = dict()


def plugin_loaded():
    settings = sublime.load_settings('tutkain.sublime-settings')

    if settings.get('debug', False):
        enable_debug()


def plugin_unloaded():
    sublime.active_window().run_command('tutkain_disconnect')
    sessions.wipe()


def print_characters(view, characters):
    if characters is not None:
        view.run_command('append', {
            'characters': characters,
            'scroll_to_end': True
        })


def append_to_view(view_name, string):
    view = view_registry.get(view_name)

    if view and string:
        view.set_read_only(False)
        print_characters(view, string)
        view.set_read_only(True)
        view.run_command('move_to', {'to': 'eof'})


def code_with_meta(view, region):
    file = view.file_name()
    code = view.substr(region)

    if file:
        line, column = view.rowcol(region.begin())

        return '^{:clojure.core/eval-file "%s" :line %s :column %s} %s' % (
            view.file_name(), line + 1, column + 1, code
        )
    else:
        return code


class TutkainClearOutputViewsCommand(WindowCommand):
    def run(self):
        for _, view in view_registry.items():
            view.set_read_only(False)
            view.run_command('select_all')
            view.run_command('right_delete')
            view.set_read_only(True)


class TutkainEvaluateFormCommand(TextCommand):
    def run(self, edit):
        window = self.view.window()
        session = sessions.get_by_owner(window.id(), 'user')

        if session is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            for region in self.view.sel():
                eval_region = region if not region.empty() else (
                    sexp.outermost(self.view, region.begin(), ignore={'comment'}).extent()
                )

                code = self.view.substr(eval_region)

                session.output({'in': code})

                log.debug({
                    'event': 'send',
                    'scope': 'form',
                    'code': code
                })

                session.send(
                    {'op': 'eval',
                     'code': code_with_meta(self.view, eval_region),
                     'file': self.view.file_name(),
                     'ns': namespace.find_declaration(self.view)}
                )


class TutkainEvaluateViewCommand(TextCommand):
    def handler(self, session, response):
        if 'err' in response:
            session.output(response)
            self.view.window().status_message('[Tutkain] View evaluation failed.')
            session.denounce(response)
        elif 'nrepl.middleware.caught/throwable' in response:
            session.output(response)
        elif response.get('status') == ['done']:
            if not session.is_denounced(response):
                self.view.window().status_message('[Tutkain] View evaluated.')

    def run(self, edit):
        window = self.view.window()
        session = sessions.get_by_owner(window.id(), 'user')

        if session is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            session.send(
                {'op': 'eval',
                 'code': code_with_meta(self.view, sublime.Region(0, self.view.size())),
                 'file': self.view.file_name()},
                handler=lambda response: self.handler(session, response)
            )


class TutkainRunTestsInCurrentNamespaceCommand(TextCommand):
    def evaluate_view(self, session, response):
        if response.get('status') == ['done']:
            session.send(
                {'op': 'eval',
                 'code': code_with_meta(self.view, sublime.Region(0, self.view.size())),
                 'file': self.view.file_name()},
                handler=lambda response: self.run_tests(session, response)
            )

    def run_tests(self, session, response):
        if response.get('status') == ['eval-error']:
            session.denounce(response)
        elif response.get('status') == ['done']:
            file_name = self.view.file_name()
            base_name = os.path.basename(file_name) if file_name else 'NO_SOURCE_FILE'

            if not session.is_denounced(response):
                session.send(
                    {'op': 'eval',
                     'code': '''
(let [report clojure.test/report]
  (with-redefs [clojure.test/report (fn [event] (report (assoc event :file "%s")))]
    ((requiring-resolve \'clojure.test/run-tests))))
                     ''' % base_name,
                     'file': file_name}
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
                 'code': '''(run! (fn [[sym _]] (ns-unmap *ns* sym))
                              (ns-publics *ns*))''',
                 'file': self.view.file_name()},
                handler=lambda response: self.evaluate_view(session, response)
            )


class HostInputHandler(TextInputHandler):
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

    def possibilities(self, folder):
        yield os.path.join(folder, '.nrepl-port')
        yield os.path.join(folder, '.shadow-cljs', 'nrepl.port')

    def discover_ports(self):
        return [self.read_port(port_file)
                for folder in self.window.folders()
                for port_file in self.possibilities(folder)
                if os.path.isfile(port_file)]

    def next_input(self, host):
        ports = self.discover_ports()

        if len(ports) > 1:
            return PortsInputHandler(ports)
        elif len(ports) == 1:
            return PortInputHandler(ports[0][1])
        else:
            return PortInputHandler('')


class PortInputHandler(TextInputHandler):
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


class PortsInputHandler(ListInputHandler):
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


class TutkainEvaluateInputCommand(WindowCommand):
    def eval(self, code):
        session = sessions.get_by_owner(self.window.id(), 'user')

        if session is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            session.output({'in': code})

            session.send({
                'op': 'eval',
                'code': code,
                'ns': namespace.find_declaration(self.window.active_view())
            })

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


class TutkainConnectCommand(WindowCommand):
    def create_output_view(self, name, host, port):
        view = self.window.new_file()
        view.set_name('REPL | *{}* | {}:{}'.format(name, host, port))
        view.settings().set('line_numbers', False)
        view.settings().set('gutter', False)
        view.settings().set('is_widget', True)
        view.settings().set('scroll_past_end', False)
        view.set_read_only(True)
        view.set_scratch(True)
        return view

    def set_session_versions(self, sessions, response):
        for session in sessions:
            session.nrepl_version = response.get('versions').get('nrepl')

        session.output(response)

    def print_loop(self, recvq):
        while True:
            item = recvq.get()

            if item is None:
                break

            log.debug({'event': 'printer/recv', 'data': item})

            # How can I de-uglify this?

            if {'value',
                'nrepl.middleware.caught/throwable',
                'in'} & item.keys():
                append_to_view('result', formatter.format(item))
            elif 'versions' in item.keys():
                append_to_view('result', formatter.format(item))
                append_to_view('out', formatter.format(item))
            elif 'status' in item and 'namespace-not-found' in item['status']:
                append_to_view('result', ':namespace-not-found')
            elif item.get('status') == ['done']:
                append_to_view('result', '\n')
            else:
                append_to_view('out', formatter.format(item))

        log.debug({'event': 'thread/exit'})

    def configure_output_views(self, host, port):
        # Set up a two-row layout.
        #
        # TODO: Make configurable? This will clobber pre-existing layouts —
        # maybe add a setting for toggling this bit?
        self.window.set_layout({
            'cells': [[0, 0, 1, 1], [0, 1, 1, 2]],
            'cols': [0.0, 1.0],
            'rows': [0.0, 0.5, 1.0]
        })

        active_view = self.window.active_view()

        out = self.create_output_view('out', host, port)
        result = self.create_output_view('result', host, port)
        result.assign_syntax('Clojure.sublime-syntax')

        # Move the result and out views into the second row.
        self.window.set_view_index(result, 1, 0)
        self.window.set_view_index(out, 1, 1)

        # Activate the result view and the view that was active prior to
        # creating the output views.
        self.window.focus_view(result)
        self.window.focus_view(active_view)

        view_registry['out'] = out
        view_registry['result'] = result

    def run(self, host, port):
        window = self.window

        try:
            client = Client(host, int(port)).go()

            plugin_session = client.clone_session()
            sessions.register(window.id(), 'plugin', plugin_session)

            user_session = client.clone_session()
            sessions.register(window.id(), 'user', user_session)

            self.configure_output_views(host, port)

            # Start a worker thread that reads items from a queue and prints
            # them into an output panel.
            print_loop = Thread(
                daemon=True,
                target=self.print_loop,
                args=(client.recvq,)
            )

            print_loop.name = 'tutkain.print_loop'
            print_loop.start()

            plugin_session.send(
                {'op': 'describe'},
                handler=lambda response: (
                    self.set_session_versions(
                        [plugin_session, user_session],
                        response
                    )
                )
            )
        except ConnectionRefusedError:
            window.status_message(
                'ERR: connection to {}:{} refused.'.format(host, port)
            )

    def input(self, args):
        return HostInputHandler(self.window)


class TutkainDisconnectCommand(WindowCommand):
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

            active_view = window.active_view()

            for _, view in view_registry.items():
                view.close()

            window.set_layout({
                'cells': [[0, 0, 1, 1]],
                'cols': [0.0, 1.0],
                'rows': [0.0, 1.0]
            })

            window.focus_view(active_view)


class TutkainNewScratchViewCommand(WindowCommand):
    def run(self):
        view = self.window.new_file()
        view.set_name('*scratch*')
        view.set_scratch(True)
        view.assign_syntax('Clojure.sublime-syntax')
        self.window.focus_view(view)


class TutkainViewEventListener(ViewEventListener):
    def on_pre_close(self):
        view = self.view

        if view == view_registry.get('result') or view == view_registry.get('out'):
            window = view.window()

            if window:
                sessions.terminate(window.id())


class TutkainExpandSelectionCommand(TextCommand):
    def run(self, edit):
        view = self.view
        selection = view.sel()

        # TODO: Add proper support for multiple cursors.
        for region in selection:
            point = region.begin()

            if not region.empty():
                view.run_command('expand_selection', {'to': 'scope'})
            else:
                if sexp.is_next_to_expand_anchor(view, point):
                    selection.add(
                        sexp.innermost(view, point).extent()
                    )
                else:
                    view.run_command('expand_selection', {'to': 'scope'})


class TutkainActivateResultViewCommand(WindowCommand):
    def run(self):
        view = view_registry.get('result')

        if view:
            active_view = self.window.active_view()
            self.window.focus_view(view)
            self.window.focus_view(active_view)


class TutkainActivateOutputViewCommand(WindowCommand):
    def run(self):
        view = view_registry.get('out')

        if view:
            active_view = self.window.active_view()
            self.window.focus_view(view)
            self.window.focus_view(active_view)


class TutkainInterruptEvaluationCommand(WindowCommand):
    def run(self):
        session = sessions.get_by_owner(self.window.id(), 'user')

        if session is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            log.debug({'event': 'eval/interrupt', 'id': session.id})
            session.send({'op': 'interrupt'})


class TutkainInsertNewlineCommand(TextCommand):
    def run(self, edit):
        if 'Clojure' in self.view.settings().get('syntax'):
            indent.insert_newline_and_indent(self.view, edit)


class TutkainIndentRegionCommand(TextCommand):
    def run(self, edit, scope='outermost', prune=False):
        if 'Clojure' in self.view.settings().get('syntax'):
            for region in self.view.sel():
                if region.empty():
                    if scope == 'outermost':
                        s = sexp.outermost(self.view, region.begin())
                    elif scope == 'innermost':
                        s = sexp.innermost(self.view, region.begin())

                    if s:
                        indent.indent_region(self.view, edit, s.extent(), prune=prune)
                else:
                    indent.indent_region(self.view, edit, region, prune=prune)


class TutkainPareditForwardCommand(TextCommand):
    def run(self, edit):
        paredit.move(self.view, True)


class TutkainPareditBackwardCommand(TextCommand):
    def run(self, edit):
        paredit.move(self.view, False)


class TutkainPareditOpenRoundCommand(TextCommand):
    def run(self, edit):
        paredit.open_bracket(self.view, edit, '(')


class TutkainPareditCloseRoundCommand(TextCommand):
    def run(self, edit):
        paredit.close_bracket(self.view, edit, ')')


class TutkainPareditOpenSquareCommand(TextCommand):
    def run(self, edit):
        paredit.open_bracket(self.view, edit, '[')


class TutkainPareditCloseSquareCommand(TextCommand):
    def run(self, edit):
        paredit.close_bracket(self.view, edit, ']')


class TutkainPareditOpenCurlyCommand(TextCommand):
    def run(self, edit):
        paredit.open_bracket(self.view, edit, '{')


class TutkainPareditCloseCurlyCommand(TextCommand):
    def run(self, edit):
        paredit.close_bracket(self.view, edit, '}')


class TutkainPareditDoubleQuoteCommand(TextCommand):
    def run(self, edit):
        paredit.double_quote(self.view, edit)


class TutkainPareditForwardSlurpCommand(TextCommand):
    def run(self, edit):
        paredit.forward_slurp(self.view, edit)


class TutkainPareditBackwardSlurpCommand(TextCommand):
    def run(self, edit):
        paredit.backward_slurp(self.view, edit)


class TutkainPareditForwardBarfCommand(TextCommand):
    def run(self, edit):
        paredit.forward_barf(self.view, edit)


class TutkainPareditBackwardBarfCommand(TextCommand):
    def run(self, edit):
        paredit.backward_barf(self.view, edit)


class TutkainPareditWrapRoundCommand(TextCommand):
    def run(self, edit):
        paredit.wrap_bracket(self.view, edit, '(')


class TutkainPareditWrapSquareCommand(TextCommand):
    def run(self, edit):
        paredit.wrap_bracket(self.view, edit, '[')


class TutkainPareditWrapCurlyCommand(TextCommand):
    def run(self, edit):
        paredit.wrap_bracket(self.view, edit, '{')


class TutkainPareditForwardDeleteCommand(TextCommand):
    def run(self, edit):
        paredit.forward_delete(self.view, edit)


class TutkainPareditBackwardDeleteCommand(TextCommand):
    def run(self, edit):
        paredit.backward_delete(self.view, edit)


class TutkainPareditRaiseSexpCommand(TextCommand):
    def run(self, edit):
        paredit.raise_sexp(self.view, edit)


class TutkainPareditSpliceSexpCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp(self.view, edit)


class TutkainPareditCommentDwimCommand(TextCommand):
    def run(self, edit):
        paredit.comment_dwim(self.view, edit)


class TutkainPareditKillCommand(TextCommand):
    def run(self, edit):
        paredit.kill(self.view, edit)


class TutkainPareditSemicolonCommand(TextCommand):
    def run(self, edit):
        paredit.semicolon(self.view, edit)


class TutkainPareditSpliceSexpKillingForwardCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp_killing_forward(self.view, edit)


class TutkainPareditSpliceSexpKillingBackwardCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp_killing_backward(self.view, edit)


class TutkainPareditForwardKillElementCommand(TextCommand):
    def run(self, edit):
        paredit.kill_element(self.view, edit, True)


class TutkainPareditBackwardKillElementCommand(TextCommand):
    def run(self, edit):
        paredit.kill_element(self.view, edit, False)


class TutkainCycleCollectionTypeCommand(TextCommand):
    def run(self, edit):
        sexp.cycle_collection_type(self.view, edit)
