import queue
import socket
from threading import Thread, Event, Lock

from . import bencode
from .log import log


repl_clients = {}


def get(id):
    global repl_clients
    repl = repl_clients.get(id)
    return repl


def register(id, repl_client):
    global repl_clients
    repl_clients[id] = repl_client
    return repl_clients


def deregister(id):
    global repl_clients
    repl_clients.pop(id, None)
    return repl_clients


def deregister_all():
    global repl_clients
    repl_clients = {}
    return repl_clients


def get_all():
    global repl_clients
    return repl_clients


class Session():
    def __init__(self, id):
        self.id = id
        self.op_count = 0
        self.lock = Lock()

    def op_id(self):
        with self.lock:
            self.op_count += 1

        return self.op_count

    def eval_op(self, opts):
        return {
            'op': 'eval',
            'id': self.op_id(),
            'nrepl.middleware.caught/print?': 'true',
            'session': self.id,
            'code': opts.get('code')
        }


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

    sessions = dict()

    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.buffer = self.socket.makefile(mode='rwb')
        log.debug({'event': 'socket/connect', 'host': host, 'port': port})

    def disconnect(self):
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                log.debug({'event': 'socket/disconnect'})
            except OSError as e:
                log.debug({'event': 'error', 'exception': e})

    def __init__(self, host, port):
        self.connect(host, port)
        self.input = queue.Queue()
        self.output = queue.Queue()
        self.stop_event = Event()

    def clone_sessions(self):
        self.input.put({'op': 'clone'})
        self.sessions['plugin'] = Session(self.output.get().get('new-session'))

        log.debug({
            'event': 'new-session/plugin',
            'id': self.sessions['plugin'].id
        })

        self.input.put({'op': 'clone'})
        self.sessions['user'] = Session(self.output.get().get('new-session'))

        log.debug({
            'event': 'new-session/user',
            'id': self.sessions['user'].id
        })

    def describe(self):
        self.input.put({
            'op': 'describe',
            'session': self.sessions['plugin'].id
        })

    def go(self):
        eval_loop = Thread(daemon=True, target=self.eval_loop)
        eval_loop.name = 'tutkain.repl_client.eval_loop'
        eval_loop.start()

        read_loop = Thread(daemon=True, target=self.read_loop)
        read_loop.name = 'tutkain.repl_client.read_loop'
        read_loop.start()

        self.clone_sessions()

    handlers = dict()

    def eval(self, code, session_key='user', handler=None):
        op = self.sessions[session_key].eval_op({'code': code})

        if handler:
            self.handlers[(op['session'], op['id'])] = handler

        self.input.put(op)

    def __enter__(self):
        self.go()
        return self

    def eval_loop(self):
        while True:
            item = self.input.get()
            if item is None:
                break

            bencode.write(self.buffer, item)

        log.debug({'event': 'thread/exit'})

    def handle(self, item):
        key = (item.get('session'), (item.get('id')))
        handler = self.handlers.get(key) or self.output.put

        try:
            handler.__call__(item)
        finally:
            if item.get('status') == ['done']:
                self.handlers.pop(key, None)

    def read_loop(self):
        try:
            while not self.stop_event.is_set():
                item = bencode.read(self.buffer)
                log.debug({'event': 'socket/read', 'item': item})
                self.handle(item)
        except OSError as e:
            log.error({
                'event': 'error',
                'exception': e
            })
        finally:
            # If we receive a stop event, put a None into the queue to tell
            # consumers to stop reading it.
            self.output.put_nowait(None)
            log.debug({'event': 'thread/exit'})

            # We've exited the loop that reads from the socket, so we can
            # close the connection to the socket.
            self.disconnect()

    def halt(self):
        # Feed poison pill to input queue.
        self.input.put(None)

        # Trigger the kill switch to tell background threads to stop reading
        # from the socket.
        self.stop_event.set()

    def __exit__(self, type, value, traceback):
        self.halt()
