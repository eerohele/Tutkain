import glob
import json
import os
import sublime
import uuid

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
from . import info
from . import repl_history

from .log import enable_debug, log
from .repl import Client


view_registry = {}


def make_color_scheme(cache_dir):
    '''
    Add the tutkain.repl.standard-streams scope into the current color scheme.

    We want stdout/stderr messages in the same REPL output view as evaluation results, but we don't
    want them to be use syntax highlighting. We can use view.add_regions() to add a scope to such
    messages such that they are not highlighted. Unfortunately, it is not possible to use
    view.add_regions() to only set the foreground color of a region. Furthermore, if we set the
    background color of the scope to use exactly the same color as the global background color of
    the color scheme, Sublime Text refuses to apply the scope.

    We therefore have to resort to this awful hack where every time the plugin is loaded or the
    color scheme changes, we generate a new color scheme in the Sublime Text cache directory. That
    color scheme defines the tutkain.repl.standard-streams scope which has an almost-transparent
    background color, creating the illusion that we're only setting the foreground color of the
    text.

    Yeah. So, please go give this issue a thumbs-up:

    https://github.com/sublimehq/sublime_text/issues/817
    '''
    view = sublime.active_window().active_view()

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    if view:
        color_scheme = view.settings().get('color_scheme')

        if color_scheme:
            (scheme_name, _) = os.path.splitext(os.path.basename(color_scheme))

            scheme_path = os.path.join(cache_dir, '{}.sublime-color-scheme'.format(scheme_name))

            if not os.path.isfile(scheme_path):
                with open(scheme_path, 'w') as scheme_file:
                    scheme_file.write(
                        json.dumps({
                            'rules': [{
                                'name': 'Tutkain REPL Standard Streams',
                                'scope': 'tutkain.repl.standard-streams',
                                'background': 'rgba(0, 0, 0, 0.01)'
                            }]
                        })
                    )


def plugin_loaded():
    settings = sublime.load_settings('tutkain.sublime-settings')
    preferences = sublime.load_settings('Preferences.sublime-settings')

    cache_dir = os.path.join(sublime.cache_path(), 'tutkain')

    # Clean up any custom color schemes we've previously created.
    for filename in glob.glob('{}/*.sublime-color-scheme'.format(cache_dir)):
        os.remove(filename)

    make_color_scheme(cache_dir)
    preferences.add_on_change('tutkain', lambda: make_color_scheme(cache_dir))

    if settings.get('debug', False):
        enable_debug()


def plugin_unloaded():
    for window in sublime.windows():
        window.run_command('tutkain_disconnect')

    sessions.wipe()

    preferences = sublime.load_settings('Preferences.sublime-settings')
    preferences.clear_on_change('tutkain')


def print_characters(view, characters):
    if characters is not None:
        view.run_command('append', {
            'characters': characters,
            'scroll_to_end': True
        })


def append_to_view(window_id, characters):
    view = view_registry.get(window_id)

    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command('move_to', {'to': 'eof'})


class TutkainClearOutputViewCommand(WindowCommand):
    def run(self):
        view = view_registry.get(self.window.id())

        if view:
            view.set_read_only(False)
            view.run_command('select_all')
            view.run_command('right_delete')
            view.set_read_only(True)


def get_eval_region(view, region, scope='outermost'):
    assert scope in {'innermost', 'outermost'}

    if not region.empty():
        return region
    else:
        if scope == 'outermost':
            outermost = sexp.outermost(view, region.begin(), ignore={'comment'})

            if outermost:
                return outermost.extent()
        elif scope == 'innermost':
            innermost = sexp.innermost(view, region.begin(), edge=True)

            if innermost:
                return innermost.extent()


class TutkainEvaluateFormCommand(TextCommand):
    def run(self, edit, scope='outermost'):
        window = self.view.window()
        session = sessions.get_by_owner(window.id(), 'user')

        if session is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            for region in self.view.sel():
                eval_region = get_eval_region(self.view, region, scope=scope)

                if eval_region:
                    code = self.view.substr(eval_region)
                    ns = namespace.find_declaration(self.view)

                    session.output({
                        'in': code,
                        'ns': ns
                    })

                    log.debug({
                        'event': 'send',
                        'scope': 'form',
                        'code': code,
                        'ns': ns
                    })

                    session.send(
                        {'op': 'eval',
                         'code': self.view.substr(eval_region),
                         'file': self.view.file_name(),
                         'ns': ns}
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
            op = {'op': 'load-file',
                  'file': self.view.substr(sublime.Region(0, self.view.size()))}

            file_path = self.view.file_name()

            if file_path:
                op['file-name'] = os.path.basename(file_path)
                op['file-path'] = file_path

            session.send(op, handler=lambda response: self.handler(session, response))


class TutkainRunTestsInCurrentNamespaceCommand(TextCommand):
    def evaluate_view(self, session, response):
        if response.get('status') == ['done']:
            session.send(
                {'op': 'eval',
                 'code': self.view.substr(sublime.Region(0, self.view.size())),
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
    def eval(self, session, code):
        session.output({'in': code})
        session.send({'op': 'eval', 'code': code})
        repl_history.update(self.window, code)

    def noop(*args):
        pass

    def run(self):
        session = sessions.get_by_owner(self.window.id(), 'user')

        if session is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            view = self.window.show_input_panel(
                'Input: ',
                repl_history.get(self.window),
                lambda code: self.eval(session, code),
                self.noop,
                self.noop
            )

            view.settings().set('tutkain_repl_input_panel', True)
            view.assign_syntax('Clojure.sublime-syntax')


class TutkainConnectCommand(WindowCommand):
    def create_output_view(self, host, port):
        view = self.window.new_file()
        view.set_name('REPL | {}:{}'.format(host, port))
        view.settings().set('line_numbers', False)
        view.settings().set('gutter', False)
        view.settings().set('is_widget', True)
        view.settings().set('scroll_past_end', False)
        view.set_read_only(True)
        view.set_scratch(True)
        return view

    def set_session_info(self, sessions, response):
        for session in sessions:
            session.info = response

        session.output(response)

    def print_loop(self, recvq):
        window_id = self.window.id()

        while True:
            item = recvq.get()

            if item is None:
                break

            log.debug({'event': 'printer/recv', 'data': item})

            # How can I de-uglify this?

            if {'value',
                'nrepl.middleware.caught/throwable',
                'in'} & item.keys():
                append_to_view(window_id, formatter.format(item))
            elif 'versions' in item:
                append_to_view(window_id, formatter.format(item))
            elif 'status' in item and 'namespace-not-found' in item['status']:
                append_to_view(window_id, ':namespace-not-found')
            elif item.get('status') == ['done']:
                append_to_view(window_id, '\n')
            else:
                characters = formatter.format(item)
                view = view_registry.get(window_id)

                if view and characters:
                    append_to_view(window_id, characters)

                    size = view.size()
                    key = str(uuid.uuid4())
                    regions = [sublime.Region(size - len(characters), size)]

                    view.add_regions(
                        key,
                        regions,
                        scope='tutkain.repl.standard-streams',
                        flags=sublime.DRAW_NO_OUTLINE
                    )

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

        output = self.create_output_view(host, port)
        output.assign_syntax('Clojure.sublime-syntax')

        # Move the output view into the second row.
        self.window.set_view_index(output, 1, 0)

        # Activate the output view and the view that was active prior to
        # creating the output view.
        self.window.focus_view(output)
        self.window.focus_view(active_view)

        view_registry[self.window.id()] = output

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
                    self.set_session_info(
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
        window_id = window.id()
        session = sessions.get_by_owner(window_id, 'plugin')

        if session is not None:
            session.output({'out': 'Disconnecting...\n'})
            session.terminate()
            user_session = sessions.get_by_owner(window_id, 'user')
            user_session.terminate()
            sessions.deregister(window_id)
            window.status_message('REPL disconnected.')

            active_view = window.active_view()

            view = view_registry.get(window_id)
            if view:
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


COMPLETION_KINDS = {
    'function': sublime.KIND_FUNCTION,
    'var': sublime.KIND_VARIABLE,
    'macro': (sublime.KIND_ID_FUNCTION, 'm', 'macro'),
    'namespace': sublime.KIND_NAMESPACE,
    'class': sublime.KIND_TYPE,
    'special-form': (sublime.KIND_ID_FUNCTION, 's', 'special form'),
    'method': sublime.KIND_FUNCTION,
    'static-method': sublime.KIND_FUNCTION
}


class TutkainViewEventListener(ViewEventListener):
    def completion_item(self, item):
        return sublime.CompletionItem(
            item.get('candidate'),
            kind=COMPLETION_KINDS.get(item.get('type'), sublime.KIND_AMBIGUOUS)
        )

    def handle_completions(self, completion_list, response):
        completions = map(self.completion_item, response.get('completions', []))
        completion_list.set_completions(completions, flags=sublime.INHIBIT_WORD_COMPLETIONS)

    def on_query_completions(self, prefix, locations):
        # CompletionList requires Sublime Text >= 4050, hence the try/except.
        try:
            point = locations[0]

            # TODO: Does this make sense?
            if self.view.match_selector(point, 'source.clojure'):
                session = sessions.get_by_owner(self.view.window().id(), 'plugin')

                if session and session.supports('completions'):
                    scope = sexp.extract_scope(self.view, point - 1)

                    if scope:
                        prefix = self.view.substr(scope)

                    completion_list = sublime.CompletionList()

                    session.send(
                        {
                            'op': 'completions',
                            'prefix': prefix,
                            'ns': namespace.find_declaration(self.view)
                        },
                        handler=lambda response: self.handle_completions(completion_list, response)
                    )

                    return completion_list
        except NameError:
            pass


class TutkainEventListener(EventListener):
    def on_hover(self, view, point, hover_zone):
        if view.match_selector(point, 'source.clojure'):
            symbol = view.substr(sexp.extract_symbol(view, point))

            if symbol:
                session = sessions.get_by_owner(view.window().id(), 'plugin')

                # TODO: Cache lookup results?
                if session and session.supports('lookup'):
                    session.send(
                        {
                            'op': 'lookup',
                            'sym': symbol,
                            'ns': namespace.find_declaration(view)
                        },
                        handler=lambda response: info.show_popup(view, point, response)
                    )


class TutkainExpandSelectionCommand(TextCommand):
    def run(self, edit):
        view = self.view
        selections = view.sel()

        for region in selections:
            if not region.empty() or sexp.ignore(view, region.begin()):
                view.run_command('expand_selection', {'to': 'scope'})
            else:
                element = sexp.find_adjacent_element(view, region.begin())

                if element:
                    selections.add(element)


class TutkainActivateResultViewCommand(WindowCommand):
    def run(self):
        view = view_registry.get(self.window.id())

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


class TutkainIndentSexpCommand(TextCommand):
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
