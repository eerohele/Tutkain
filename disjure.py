import sublime
import sublime_plugin
import socket
import queue
from threading import Thread, Event
import logging

from functools import partial
from paredit import shared as parens

import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'dependencies'))

import edn_format
from edn_format import Keyword


def prev_char_type(view, caret_point):
    prev_char = parens.get_previous_character(view, caret_point)[1]
    return parens.char_type(prev_char)


def next_char_type(view, caret_point):
    next_char = parens.get_next_character(view, caret_point)[1]
    return parens.char_type(next_char)


def get_eval_region(view):
    region = view.sel()[0]

    if region.begin() == region.end():
        caret_point = view.sel()[0].begin()
        expr = parens.get_expression(view, caret_point)

        if not parens.is_inside_string(view, caret_point):
            if (prev_char_type(view, caret_point) == 'rbracket'):
                expr = parens.get_previous_expression(view, caret_point)
            elif (next_char_type(view, caret_point) == 'lbracket'):
                expr = parens.get_next_expression(view, caret_point)

        return sublime.Region(*expr)
    else:
        return region


def append_to_output_panel(window, characters):
    panel = window.find_output_panel('panel')

    panel.set_read_only(False)
    panel.run_command('append', {
        'characters': characters.strip() + '\n',
        'scroll_to_end': True
    })
    panel.set_read_only(True)

    panel.run_command('move_to', {'to': 'eof'})


class DisjureEvaluateFormCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global repl_client

        if repl_client is None:
            self.view.window().status_message('ERR: Not connected to a REPL.')
        else:
            region = get_eval_region(self.view)
            chars = self.view.substr(region)
            append_to_output_panel(self.view.window(), '=> ' + chars)
            logging.debug({'event': 'send', 'scope': 'form', 'data': chars})
            repl_client.input.put(chars)


class DisjureEvaluateViewCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        global repl_client

        region = sublime.Region(0, self.view.size())
        chars = self.view.substr(region)
        repl_client.input.put(chars)


class HostInputHandler(sublime_plugin.TextInputHandler):
    window = None

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
    window = None

    def __init__(self, window):
        self.window = window

    def placeholder(self):
        return 'Port'

    def validate(self, text):
        return text.isdigit()

    def find_prepl_port_file(self):
        # Propel writes the port it uses into a file called '.prepl-port' when
        # the user sets the --write-port-file option.
        #
        # Find the first project directory that has a file called '.prepl-port'
        # in the root directory of the project.
        folders = self.window.folders()
        options = map(lambda f: os.path.join(f, '.prepl-port'), folders)
        return next((x for x in options if os.path.isfile(x)), None)

    def initial_text(self):
        prepl_port = self.find_prepl_port_file()

        if prepl_port:
            return open(prepl_port, 'r').read()
        else:
            return None


class DisjureToggleOutputPanelCommand(sublime_plugin.WindowCommand):
    def run(self):
        active_panel = self.window.active_panel()
        panel = 'output.panel'

        if active_panel == panel:
            self.window.run_command('hide_panel', {'panel': panel})
        else:
            self.window.run_command('show_panel', {'panel': panel})


class ReplClient(object):
    def connect(self, host, port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((host, port))
        logging.debug({'event': 'socket/connect', 'host': host, 'port': port})

    def disconnect(self):
        if self.connection is not None:
            self.connection.shutdown(socket.SHUT_RDWR)
            self.connection.close()
            logging.debug({'event': 'socket/disconnect'})

    def __init__(self, host, port):
        self.connect(host, port)
        self.input = queue.Queue()
        self.output = queue.Queue()
        self.stop_event = Event()

    def go(self):
        Thread(daemon=True, target=self.eval_loop).start()
        Thread(daemon=True, target=self.read_loop).start()

    def __enter__(self):
        self.go()
        return self

    def eval_loop(self):
        while True:
            item = self.input.get()
            if item is None:
                break

            self.connection.sendall(str.encode(item))

        logging.debug({'event': 'thread/exit', 'thread': 'eval_loop'})

    def read_loop(self):
        """Read lines of EDN values from a socket connection, parse them, and
        put them into a queue. If the stop event is set, exit.
        """
        try:
            while not self.stop_event.wait(0):
                bytes = []

                # Read from the socket one byte at a time and append the byte
                # into an array. If the byte is a newline, stop reading.
                for data in iter(partial(self.connection.recv, 1), b'\n'):
                    bytes.append(data)

                chars = ''.join(map(lambda b: b.decode('utf-8'), bytes))
                logging.debug({'event': 'recv', 'data': chars})
                self.output.put(edn_format.loads(chars))
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

        self.disconnect()

    def __exit__(self, type, value, traceback):
        self.halt()


class DisjureEvaluateInputCommand(sublime_plugin.WindowCommand):
    def eval(self, input):
        global repl_client

        if repl_client is None:
            self.window.status_message('ERR: Not connected to a REPL.')
        else:
            self.window.run_command('show_panel', {'panel': 'output.panel'})
            append_to_output_panel(self.window, '=> ' + input)
            repl_client.input.put(input)

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


class DisjureConnectToSocketReplCommand(sublime_plugin.WindowCommand):
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

            append_to_output_panel(self.window, item.get(Keyword('val')))

        logging.debug({'event': 'thread/exit', 'thread': 'print_loop'})

    def run(self, host, port):
        global repl_client

        try:
            repl_client = ReplClient(host, int(port))
            repl_client.go()

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
            connection = None

            self.window.status_message(
                'ERR: socket to {}:{} refused.'.format(host, port)
            )

    def input(self, args):
        return HostInputHandler(self.window)


class DisjureDisconnectFromSocketReplCommand(sublime_plugin.WindowCommand):
    def run(self):
        global repl_client

        repl_client.halt()
        repl_client = None

        append_to_output_panel(self.window, 'Disconnected.')
