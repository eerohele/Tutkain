import base64
import collections
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

from . import selectors
from . import sexp
from . import forms
from . import formatter
from . import indent
from . import paredit
from . import namespace
from .repl import info
from .repl import history
from .repl.client import Client
from .repl.session import Session

from .log import log, start_logging, stop_logging


state = {'sessions_by_view': collections.defaultdict(dict)}


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
                                'name': 'Tutkain REPL Standard Output',
                                'scope': 'tutkain.repl.stdout',
                                'background': 'rgba(0, 0, 0, 0.01)'
                            }, {
                                'name': 'Tutkain REPL Standard Error',
                                'scope': 'tutkain.repl.stderr',
                                'background': 'rgba(0, 0, 0, 0.01)',
                                'foreground': view.style().get('redish', 'crimson')
                            }]
                        })
                    )


def plugin_loaded():
    settings = sublime.load_settings('tutkain.sublime-settings')

    start_logging(settings.get('debug', False))

    preferences = sublime.load_settings('Preferences.sublime-settings')

    cache_dir = os.path.join(sublime.cache_path(), 'tutkain')

    # Clean up any custom color schemes we've previously created.
    for filename in glob.glob('{}/*.sublime-color-scheme'.format(cache_dir)):
        os.remove(filename)

    make_color_scheme(cache_dir)
    preferences.add_on_change('tutkain', lambda: make_color_scheme(cache_dir))


def plugin_unloaded():
    stop_logging()

    for window in sublime.windows():
        window.run_command('tutkain_disconnect')

    preferences = sublime.load_settings('Preferences.sublime-settings')
    preferences.clear_on_change('tutkain')


def print_characters(view, characters):
    if characters is not None:
        view.run_command('append', {
            'characters': characters,
            'scroll_to_end': True
        })


def append_to_view(view, characters):
    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command('move_to', {'to': 'eof'})


def test_region_key(view, result_type):
    return '{}:{}'.format(view.file_name(), result_type)


def get_active_repl_view():
    return state.get('active_repl_view')


def get_view_sessions(view):
    return view and state['sessions_by_view'].get(view.id())


def get_active_view_sessions():
    return get_view_sessions(get_active_repl_view())


def get_session_by_owner(owner):
    sessions = get_active_view_sessions()
    return sessions and sessions.get(owner)


class TutkainClearOutputViewCommand(WindowCommand):
    def clear_view(self, view):
        if view:
            view.set_read_only(False)
            view.run_command('select_all')
            view.run_command('right_delete')
            view.set_read_only(True)

    def run(self):
        session = get_session_by_owner('plugin')

        if session:
            self.clear_view(session.view)

        self.clear_view(self.window.find_output_panel('tutkain'))


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
        session = get_session_by_owner('user')

        if session is None:
            self.view.window().status_message('ERR: Not connected to a REPL.')
        else:
            for region in self.view.sel():
                eval_region = get_eval_region(self.view, region, scope=scope)

                if eval_region:
                    code = self.view.substr(eval_region)
                    ns = namespace.find_declaration(self.view) or 'user'

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
            session.output({'value': ':tutkain/failed\n'})
            session.output(response)
            session.denounce(response)
        elif 'nrepl.middleware.caught/throwable' in response:
            session.output(response)
        elif response.get('status') == ['done']:
            if not session.is_denounced(response):
                session.output({'value': ':tutkain/loaded\n'})

    def run(self, edit):
        window = self.view.window()
        session = get_session_by_owner('user')

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

    def annotation(self, response):
        args = {
            'reference': response['expected'],
            'actual': response['actual']
        }

        return '''
        <a style="font-size: 0.8rem"
           href='{}'>{}</a>
        '''.format(
            sublime.command_url('tutkain_open_diff_window', args=args),
            'diff' if response.get('type', 'fail') == 'fail' else 'show'
        )

    def add_markers(self, session, response):
        if 'status' not in response:
            self.view.run_command('tutkain_clear_test_markers')

        results = {'fail': {}, 'error': {}, 'pass': {}}

        if 'fail' in response:
            for result in response['fail']:
                line = result['line'] - 1
                point = self.view.text_point(line, 0)

                results['fail'][line] = {
                    'type': result['type'],
                    'region': sublime.Region(point, point),
                    'expected': result['expected'],
                    'actual': result['actual']
                }

        if 'error' in response:
            for result in response['error']:
                line = result['var-meta']['line'] - 1
                column = result['var-meta']['column'] - 1
                point = self.view.text_point(line, column)

                results['error'][line] = {
                    'type': result['type'],
                    'region': forms.find_next(self.view, point),
                    'expected': result['expected'],
                    'actual': result['actual']
                }

        if 'pass' in response:
            for result in response['pass']:
                line = result['line'] - 1
                point = self.view.text_point(line, 0)

                # Only add pass for line if there's no fail for the same line.
                if line not in results['fail']:
                    results['pass'][line] = {
                        'type': result['type'],
                        'region': sublime.Region(point, point)
                    }

            passes = results['pass'].values()
            if passes:
                self.view.add_regions(
                    test_region_key(self.view, 'passes'),
                    [p['region'] for p in passes],
                    scope='region.greenish',
                    icon='circle'
                )

            failures = results['fail'].values()
            if failures:
                self.view.add_regions(
                    test_region_key(self.view, 'failures'),
                    [f['region'] for f in failures],
                    scope='region.redish',
                    icon='circle',
                    annotations=[self.annotation(f) for f in failures]
                )

            errors = results['error'].values()
            if errors:
                self.view.add_regions(
                    test_region_key(self.view, 'errors'),
                    [e['region'] for e in errors],
                    scope='region.orangish',
                    icon='circle',
                    annotation_color='orange',
                    annotations=[self.annotation(e) for e in errors],
                    flags=sublime.DRAW_NO_FILL
                )

    def run_tests(self, session, response):
        if response.get('status') == ['eval-error']:
            session.denounce(response)
        elif response.get('status') == ['done']:
            if not session.is_denounced(response):
                file_name = self.view.file_name()
                base_name = os.path.basename(file_name) if file_name else 'NO_SOURCE_FILE'

                if int(sublime.version()) >= 4073 and session.supports('tutkain/test'):
                    def handler(response):
                        session.output(response)
                        self.add_markers(session, response)

                    session.send({
                        'op': 'tutkain/test',
                        'ns': namespace.find_declaration(self.view),
                        'file': base_name
                    }, handler=handler)
                else:
                    # For nREPL < 0.8 compatibility
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
        session = get_session_by_owner('plugin')

        if session is None:
            window.status_message('ERR: Not connected to a REPL.')
        else:
            session.send(
                {'op': 'eval',
                 'code': '''(->> (ns-publics *ns*)
                                 (filter (fn [[_ v]] (-> v meta :test)))
                                 (run! (fn [[sym _]] (ns-unmap *ns* sym))))''',
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
        session.output({'in': code, 'ns': session.namespace})
        session.send({'op': 'eval', 'code': code, 'ns': session.namespace})
        history.update(self.window, code)

    def noop(*args):
        pass

    def run(self):
        session = get_session_by_owner('user')

        if session is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            view = self.window.show_input_panel(
                'Input: ',
                history.get(self.window),
                lambda code: self.eval(session, code),
                self.noop,
                self.noop
            )

            view.settings().set('tutkain_repl_input_panel', True)
            view.assign_syntax('Clojure (Tutkain).sublime-syntax')


class TutkainConnectCommand(WindowCommand):
    def sideloader_provide(self, session, response):
        if 'name' in response:
            name = response['name']

            op = {
                'id': response['id'],
                'op': 'sideloader-provide',
                'type': response['type'],
                'name': name
            }

            path = os.path.join(sublime.packages_path(), 'tutkain/clojure/src', name)

            if os.path.isfile(path):
                log.debug({'event': 'sideloader/provide', 'path': path})

                with open(path, 'rb') as file:
                    op['content'] = base64.b64encode(file.read()).decode('utf-8')
            else:
                op['content'] = ''

            session.send(op, handler=lambda _: None)

    def initialize(self, session, view):
        if session.supports('sideloader-start') and session.supports('add-middleware'):
            def finalize(response):
                if response.get('status') == ['done']:
                    info = response
                    session.info = info
                    session.output(response)
                    state['sessions_by_view'][view.id()]['sideloader'] = session

                    def register_session(owner, response):
                        if response.get('status') == ['done']:
                            new_session_id = response['new-session']
                            new_session = Session(new_session_id, session.client, view)
                            new_session.info = info
                            session.client.sessions[new_session_id] = new_session
                            state['sessions_by_view'][view.id()][owner] = new_session

                    session.send(
                        {'op': 'clone', 'session': session.id},
                        handler=lambda response: register_session('plugin', response)
                    )

                    def register_user_session(response):
                        if response.get('status') == ['done']:
                            register_session('user', response)

                            sessions = state['sessions_by_view'][view.id()]

                            view.settings().set(
                                'tutkain_session_ids',
                                list(map(lambda session: session.id, sessions.values()))
                            )

                    session.send(
                        {'op': 'clone', 'session': session.id},
                        handler=lambda response: register_user_session(response)
                    )

            def add_tap(response):
                if response.get('status') == ['done']:
                    session.send({'op': 'tutkain/add-tap'})
                    session.send({'op': 'describe'}, handler=finalize)

            def add_middleware(response):
                if response.get('status') == ['done']:
                    session.send({
                        'op': 'add-middleware',
                        'middleware': [
                            'tutkain.nrepl.middleware.test/wrap-test',
                            'tutkain.nrepl.middleware.tap/wrap-tap',
                        ]
                    }, handler=add_tap)

            session.send({
                'op': 'sideloader-start'
            }, handler=lambda response: self.sideloader_provide(session, response))

            session.send({
                'op': 'eval',
                'code': '''(require 'tutkain.nrepl.util.pprint)'''
                # We use a noop handler, to prevent the printer printing the nil response of this
                # eval op.
            }, pprint=False, handler=add_middleware)

    def print(self, view, item):
        if view:
            if {'value', 'nrepl.middleware.caught/throwable', 'in', 'versions', 'summary'} & item.keys():
                append_to_view(view, formatter.format(item))
            elif 'status' in item and 'interrupted' in item['status']:
                append_to_view(view, ':tutkain/interrupted\n')
            elif 'status' in item and 'session-idle' in item['status']:
                append_to_view(view, ':tutkain/nothing-to-interrupt\n')
            elif 'status' in item and 'namespace-not-found' in item['status']:
                append_to_view(view, ':tutkain/namespace-not-found\n')
            else:
                characters = formatter.format(item)

                if characters:
                    append_to_view(view, characters)

                    size = view.size()
                    key = str(uuid.uuid4())
                    regions = [sublime.Region(size - len(characters), size)]
                    scope = 'tutkain.repl.stderr' if 'err' in item else 'tutkain.repl.stdout'

                    view.add_regions(key, regions, scope=scope, flags=sublime.DRAW_NO_OUTLINE)

    def print_loop(self, client):
        while True:
            item = client.recvq.get()

            if item is None:
                break

            log.debug({'event': 'printer/recv', 'data': item})

            session = client.sessions.get(item.get('session'))

            if session:
                if 'tap' in item and 'session' in item:
                    view = get_active_repl_view()
                    session_ids = view.settings().get('tutkain_session_ids')

                    if view and item['session'] in session_ids:
                        panel = self.window.find_output_panel('tutkain')
                        self.window.run_command('show_panel', {'panel': 'output.tutkain'})
                        append_to_view(panel, item['tap'])
                else:
                    self.print(session.view, item)

        log.debug({'event': 'thread/exit'})

    def create_output_view(self, host, port):
        # Set up a two-row layout.
        #
        # TODO: Make configurable? This will clobber pre-existing layouts —
        # maybe add a setting for toggling this bit?
        self.window.set_layout({
            'cells': [[0, 0, 1, 1], [0, 1, 1, 2]],
            'cols': [0.0, 1.0],
            'rows': [0.0, 0.75, 1.0]
        })

        active_view = self.window.active_view()

        view_count = len(self.window.views_in_group(1))
        suffix = '' if view_count == 0 else ' ({})'.format(view_count)

        view = self.window.new_file()
        view.set_name('REPL | {}:{}{}'.format(host, port, suffix))
        view.settings().set('line_numbers', False)
        view.settings().set('gutter', False)
        view.settings().set('is_widget', True)
        view.settings().set('scroll_past_end', False)
        view.settings().set('tutkain_repl_output_view', True)
        view.set_read_only(True)
        view.set_scratch(True)

        view.assign_syntax('Clojure (Tutkain).sublime-syntax')

        # Move the output view into the second row.
        self.window.set_view_index(view, 1, view_count)

        # Activate the output view and the view that was active prior to
        # creating the output view.
        self.window.focus_view(view)
        self.window.focus_view(active_view)

        return view

    def create_tap_panel(self):
        if not self.window.find_output_panel('tutkain'):
            panel = self.window.create_output_panel('tutkain')
            panel.settings().set('line_numbers', False)
            panel.settings().set('gutter', False)
            panel.settings().set('is_widget', True)
            panel.settings().set('scroll_past_end', False)
            panel.assign_syntax('Clojure (Tutkain).sublime-syntax')

    def run(self, host, port):
        window = self.window

        try:
            client = Client(host, int(port)).go()

            self.create_tap_panel()
            view = self.create_output_view(host, port)

            session = client.clone_session(view)

            # Start a worker thread that reads items from a queue and prints
            # them into an output panel.
            print_loop = Thread(
                daemon=True,
                target=self.print_loop,
                args=(client,)
            )

            print_loop.name = 'tutkain.print_loop'
            print_loop.start()

            def handler(response):
                if response.get('status') == ['done']:
                    session.info = response
                    self.initialize(session, view)

            session.send({'op': 'describe'}, handler=handler)
        except ConnectionRefusedError:
            window.status_message(
                'ERR: connection to {}:{} refused.'.format(host, port)
            )

    def input(self, args):
        return HostInputHandler(self.window)


class TutkainDisconnectCommand(WindowCommand):
    def output_views(self):
        return [
            v for v in self.window.views() if v.settings().get('tutkain_repl_output_view')
        ]

    def run(self):
        view = get_active_repl_view()

        if view:
            view.close()
        else:
            on_close_last_session(self.window)


class TutkainNewScratchViewCommand(WindowCommand):
    def run(self):
        view = self.window.new_file()
        view.set_name('*scratch*')
        view.set_scratch(True)
        view.assign_syntax('Clojure (Tutkain).sublime-syntax')
        self.window.focus_view(view)


def completion_kinds():
    if int(sublime.version()) >= 4050:
        return {
            'function': sublime.KIND_FUNCTION,
            'var': sublime.KIND_VARIABLE,
            'macro': (sublime.KIND_ID_FUNCTION, 'm', 'macro'),
            'namespace': sublime.KIND_NAMESPACE,
            'class': sublime.KIND_TYPE,
            'special-form': (sublime.KIND_ID_FUNCTION, 's', 'special form'),
            'method': sublime.KIND_FUNCTION,
            'static-method': sublime.KIND_FUNCTION
        }
    else:
        return {}


class TutkainViewEventListener(ViewEventListener):
    def completion_item(self, item):
        return sublime.CompletionItem(
            item.get('candidate'),
            kind=completion_kinds().get(item.get('type'), sublime.KIND_AMBIGUOUS)
        )

    def handle_completions(self, completion_list, response):
        completions = map(self.completion_item, response.get('completions', []))
        completion_list.set_completions(completions)

    def on_query_completions(self, prefix, locations):
        if int(sublime.version()) >= 4050:
            point = locations[0] - 1

            if self.view.match_selector(point, 'meta.symbol.clojure - meta.function.parameters'):
                session = get_session_by_owner('plugin')

                if session and session.supports('completions'):
                    scope = selectors.expand_by_selector(self.view, point, 'meta.symbol.clojure')

                    if scope:
                        prefix = self.view.substr(scope)

                    completion_list = sublime.CompletionList()

                    ns = namespace.find_declaration(self.view)

                    op = {
                        'op': 'completions',
                        'prefix': prefix
                    }

                    if ns:
                        op['ns'] = ns

                    session.send(
                        op,
                        handler=lambda response: self.handle_completions(completion_list, response)
                    )

                    return completion_list


def lookup(view, point, handler):
    is_repl_output_view = view.settings().get('tutkain_repl_output_view')

    if view.match_selector(point, 'meta.symbol.clojure') and not is_repl_output_view:
        symbol = selectors.expand_by_selector(view, point, 'meta.symbol.clojure')

        if symbol:
            session = get_session_by_owner('plugin')

            # TODO: Cache lookup results?
            if session and session.supports('lookup'):
                session.send(
                    {
                        'op': 'lookup',
                        'sym': view.substr(symbol),
                        'ns': namespace.find_declaration(view)
                    },
                    handler=handler
                )


class TutkainShowSymbolInformationCommand(TextCommand):
    def run(self, edit):
        lookup(
            self.view,
            self.view.sel()[0].begin(),
            lambda response: info.show_popup(self.view, self.view.sel()[0].begin(), response)
        )


class TutkainGotoSymbolDefinitionCommand(TextCommand):
    def run(self, edit):
        lookup(
            self.view,
            self.view.sel()[0].begin(),
            lambda response: info.goto(
                self.view.window(),
                info.parse_location(response.get('info'))
            )
        )


def on_close_last_session(window):
    # If this is the final REPL view, restore layout to single.
    window.set_layout({
        'cells': [[0, 0, 1, 1]],
        'cols': [0.0, 1.0],
        'rows': [0.0, 1.0]
    })

    # Destroy tap panel
    window.destroy_output_panel('tutkain')

    window.status_message('[Tutkain] REPL disconnected.')


class TutkainEventListener(EventListener):
    def on_activated(self, view):
        if view.settings().get('tutkain_repl_output_view'):
            state['active_repl_view'] = view

    def on_hover(self, view, point, hover_zone):
        lookup(view, point, lambda response: info.show_popup(view, point, response))

    def on_pre_close(self, view):
        if view and view.settings().get('tutkain_repl_output_view'):
            window = view.window()
            sessions = get_view_sessions(view)

            if not sessions:
                on_close_last_session(window)
            else:
                del state['sessions_by_view'][view.id()]

                def handler(response):
                    if 'status' in response and 'done' in response['status']:
                        session.client.deregister_session(
                            response['session'],
                            lambda: on_close_last_session(window)
                        )

                for session in sessions.values():
                    session.send({'op': 'close'}, handler=handler)

            if window:
                active_view = window.active_view()

                if active_view:
                    active_view.run_command('tutkain_clear_test_markers')
                    window.focus_view(active_view)


class TutkainExpandSelectionCommand(TextCommand):
    def run(self, edit):
        view = self.view
        selections = view.sel()

        for region in selections:
            if not region.empty() or selectors.ignore(view, region.begin()):
                view.run_command('expand_selection', {'to': 'scope'})
            else:
                form = forms.find_adjacent(view, region.begin())
                form and selections.add(form)


class TutkainInterruptEvaluationCommand(WindowCommand):
    def run(self):
        session = get_session_by_owner('user')

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


class TutkainPareditSemicolonCommand(TextCommand):
    def run(self, edit):
        paredit.semicolon(self.view, edit)


class TutkainPareditSpliceSexpKillingForwardCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp_killing_forward(self.view, edit)


class TutkainPareditSpliceSexpKillingBackwardCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp_killing_backward(self.view, edit)


class TutkainPareditForwardKillFormCommand(TextCommand):
    def run(self, edit):
        paredit.kill_form(self.view, edit, True)


class TutkainPareditBackwardKillFormCommand(TextCommand):
    def run(self, edit):
        paredit.kill_form(self.view, edit, False)


class TutkainPareditBackwardMoveFormCommand(TextCommand):
    def run(self, edit):
        paredit.backward_move_form(self.view, edit)


class TutkainPareditForwardMoveFormCommand(TextCommand):
    def run(self, edit):
        paredit.forward_move_form(self.view, edit)


class TutkainPareditThreadFirstCommand(TextCommand):
    def run(self, edit):
        paredit.thread_first(self.view, edit)


class TutkainPareditThreadLastCommand(TextCommand):
    def run(self, edit):
        paredit.thread_last(self.view, edit)


class TutkainCycleCollectionTypeCommand(TextCommand):
    def run(self, edit):
        sexp.cycle_collection_type(self.view, edit)


class TutkainReplHistoryListener(EventListener):
    def on_deactivated(self, view):
        if view.settings().get('tutkain_repl_input_panel'):
            history.index = None


class TutkainNavigateReplHistoryCommand(TextCommand):
    def run(self, edit, forward=False):
        history.navigate(self.view, edit, forward=forward)


class TutkainClearTestMarkersCommand(TextCommand):
    def run(self, edit):
        self.view.erase_regions(test_region_key(self.view, 'passes'))
        self.view.erase_regions(test_region_key(self.view, 'failures'))
        self.view.erase_regions(test_region_key(self.view, 'errors'))


class TutkainOpenDiffWindowCommand(TextCommand):
    def run(self, edit, reference='', actual=''):
        self.view.window().run_command('new_window')

        window = sublime.active_window()
        window.set_tabs_visible(False)
        window.set_minimap_visible(False)
        window.set_status_bar_visible(False)
        window.set_sidebar_visible(False)
        window.set_menu_visible(False)

        view = window.new_file()
        view.set_name('Tutkain: Diff')
        view.assign_syntax('Clojure (Tutkain).sublime-syntax')
        view.set_scratch(True)
        view.set_reference_document(reference)
        view.run_command('append', {'characters': actual})

        # Hackity hack to try to ensure that the inline diff is open when the diff window opens.
        #
        # I have no idea why this works, or whether it actually even works.
        view.run_command('next_modification')
        view.show(0)

        view.run_command('toggle_inline_diff')


class TutkainShowUnsuccessfulTestsCommand(TextCommand):
    def get_preview(self, region):
        line = self.view.rowcol(region.begin())[0] + 1
        return '{}: {}'.format(line, self.view.substr(self.view.line(region)).lstrip())

    def run(self, args):
        view = self.view
        failures = view.get_regions(test_region_key(view, 'failures'))
        errors = view.get_regions(test_region_key(view, 'errors'))
        regions = failures + errors

        if regions:
            regions.sort()

            def goto(i):
                view.set_viewport_position(view.text_to_layout(regions[i].begin()))

            view.window().show_quick_panel(
                [self.get_preview(region) for region in regions],
                goto,
                flags=sublime.MONOSPACE_FONT,
                on_highlight=goto
            )
