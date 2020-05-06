import sublime
import sublime_plugin
import socket
import queue
from threading import Thread, Event
import logging

import tutkain.brackets as brackets
import tutkain.bencode as bencode


def debug_mode():
    logging.basicConfig(
        level=logging.DEBUG,
        format=' %(asctime)s - %(levelname)s - %(message)s'
        )


repl_client = None


def get_eval_region(view):
    region = view.sel()[0]

    if region.empty():
        return brackets.current_form_region(view, region.begin())
    else:
        return region


def append_to_output_panel(window, characters):
    if characters is not None:
        panel = window.find_output_panel('panel')
        window.run_command('show_panel', {'panel': 'output.panel'})

        panel.set_read_only(False)
        panel.run_command('append', {
            'characters': characters.strip() + '\n',
            'scroll_to_end': True
        })
        panel.set_read_only(True)

        panel.run_command('move_to', {'to': 'eof'})


class TutkainClearOutputPanelCommand(sublime_plugin.WindowCommand):
    def run(self):
        panel = self.window.find_output_panel('panel')
        panel.set_read_only(False)
        panel.run_command('select_all')
        panel.run_command('right_delete')
        panel.set_read_only(True)


class TutkainEvaluateFormCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global repl_client

        if repl_client is None:
            self.view.window().status_message('ERR: Not connected to a REPL.')
        else:
            region = get_eval_region(self.view)
            if region is not None:
                chars = self.view.substr(region)
                append_to_output_panel(self.view.window(), '=> ' + chars)

                logging.debug({
                    'event': 'send',
                    'scope': 'form',
                    'data': chars
                })

                repl_client.input.put({
                    'op': 'eval',
                    'session': repl_client.session,
                    'code': chars
                })


class TutkainEvaluateViewCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global repl_client

        if repl_client is None:
            self.view.window().status_message('ERR: Not connected to a REPL.')
        else:
            region = sublime.Region(0, self.view.size())

            repl_client.input.put({
                'op': 'eval',
                'session': repl_client.session,
                'code': self.view.substr(region)
            })


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


class ReplClient(object):
    '''
    Here's how ReplClient works:

    1. Open a socket connection to the given host and port.
    2. Start a worker that gets items from a queue and sends them over the
       socket for evaluation.
    3. Start a worker that reads bencode strings from the socket,
       parses them, and puts them into a queue.

    Calling `halt()` on a ReplClient will stop the background threads and close
    the socket connection. ReplClient is a context manager, so you can use it
    with the `with` statement.
    '''
    session = None

    def connect(self, host, port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((host, port))
        logging.debug({'event': 'socket/connect', 'host': host, 'port': port})

    def disconnect(self):
        if self.connection is not None:
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
                self.connection.close()
                logging.debug({'event': 'socket/disconnect'})
            except OSError as e:
                logging.debug({'event': 'error', 'exception': e})

    def __init__(self, host, port):
        self.connect(host, port)
        self.input = queue.Queue()
        self.output = queue.Queue()
        self.stop_event = Event()

    def go(self):
        Thread(daemon=True, target=self.eval_loop).start()
        Thread(daemon=True, target=self.read_loop).start()

        # https://nrepl.org/nrepl/building_clients.html#_basics
        self.input.put({'op': 'clone'})
        session = self.output.get().get('new-session')
        self.session = session
        self.input.put({'op': 'describe', 'session': session})

    def __enter__(self):
        self.go()
        return self

    def eval_loop(self):
        while True:
            item = self.input.get()
            if item is None:
                break

            self.connection.sendall(bencode.write(item))

        logging.debug({'event': 'thread/exit', 'thread': 'eval_loop'})

    def read_loop(self):
        try:
            while not self.stop_event.wait(0):
                item = bencode.read(self.connection)
                logging.debug({'event': 'read', 'item': item})

                self.output.put(item)
        except OSError as e:
            logging.debug({'event': 'error', 'exception': e})
        finally:
            # If we receive a stop event, put a None into the queue to tell
            # consumers to stop reading it.
            self.output.put_nowait(None)
            logging.debug({'event': 'thread/exit', 'thread': 'read_loop'})

    def halt(self):
        # Feed poison pill to input queue.
        if self.input is not None:
            self.input.put(None)

        # Trigger the kill switch to tell background threads to stop reading
        # from the socket.
        if self.stop_event is not None:
            self.stop_event.set()

        self.session = None
        self.disconnect()

    def __exit__(self, type, value, traceback):
        self.halt()


class TutkainEvaluateInputCommand(sublime_plugin.WindowCommand):
    def eval(self, input):
        global repl_client

        if repl_client is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            self.window.run_command('show_panel', {'panel': 'output.panel'})
            append_to_output_panel(self.window, '=> ' + input)

            repl_client.input.put({
                'op': 'eval',
                'session': repl_client.session,
                'code': input
            })

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

    def print_loop(self, repl_client):
        while True:
            item = repl_client.output.get()

            if item is None:
                break
            logging.debug({'event': 'printer/recv', 'data': item})

            versions = item.get('versions')

            if versions:
                clojure_version = versions.get('clojure').get('version-string')
                nrepl_version = versions.get('nrepl').get('version-string')

                append_to_output_panel(
                    self.window,
                    'Clojure {}'.format(clojure_version)
                )

                append_to_output_panel(
                    self.window,
                    'nREPL {}'.format(nrepl_version)
                )

            append_to_output_panel(self.window, item.get('out'))
            append_to_output_panel(self.window, item.get('value'))
            append_to_output_panel(self.window, item.get('err'))

        logging.debug({'event': 'thread/exit', 'thread': 'print_loop'})

    def run(self, host, port):
        global repl_client

        try:
            repl_client = ReplClient(host, int(port))
            repl_client.go()

            # Start a worker that reads values from a ReplClient output queue
            # and prints them into an output panel.
            Thread(
                daemon=True,
                target=self.print_loop,
                args=(repl_client,)
            ).start()

            # Create an output panel for printing evaluation results and show
            # it.
            self.configure_output_panel()
            self.window.run_command('show_panel', {'panel': 'output.panel'})

            message = 'Connected to {}:{}.'.format(host, port)
            append_to_output_panel(self.window, message)
        except ConnectionRefusedError:
            self.window.status_message(
                'ERR: connection to {}:{} refused.'.format(host, port)
            )

    def input(self, args):
        return HostInputHandler(self.window)


class TutkainDisconnectCommand(sublime_plugin.WindowCommand):
    def run(self):
        global repl_client

        if repl_client is not None:
            repl_client.halt()
            repl_client = None

            append_to_output_panel(self.window, 'Disconnected.')
