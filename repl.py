import queue
import socket
from threading import Thread, Event, Lock

from . import bencode
from .log import log


class ClientRegistry():
    clients = {}

    @staticmethod
    def get(id):
        client = ClientRegistry.clients.get(id)
        return client

    @staticmethod
    def register(id, client):
        ClientRegistry.clients[id] = client
        return ClientRegistry.clients

    @staticmethod
    def deregister(id):
        ClientRegistry.clients.pop(id, None)
        return ClientRegistry.clients

    @staticmethod
    def deregister_all():
        ClientRegistry.clients = {}
        return ClientRegistry.clients

    @staticmethod
    def get_all():
        return ClientRegistry.clients


class Session():
    handlers = dict()
    errors = dict()

    def __init__(self, id):
        self.id = id
        self.op_count = 0
        self.lock = Lock()

    def op_id(self):
        with self.lock:
            self.op_count += 1

        return self.op_count

    def mkop(self, op):
        op['session'] = self.id
        op['id'] = self.op_id()
        op['nrepl.middleware.caught/print?'] = 'true'
        op['nrepl.middleware.print/stream?'] = 'true'
        return op

    def denounce(self, response):
        id = response.get('id')

        if id:
            self.errors[id] = response

    def is_denounced(self, response):
        return response.get('id') in self.errors


class Client(object):
    '''
    Here's how Client works:

    1. Open a socket connection to the given host and port.
    2. Start a worker that gets items from a queue and sends them over the
       socket for evaluation.
    3. Start a worker that reads bencode strings from the socket,
       parses them, and puts them into a queue.

    Calling `halt()` on a Client will stop the background threads and close
    the socket connection. Client is a context manager, so you can use it
    with the `with` statement.
    '''

    sessions_by_owner = dict()
    sessions_by_id = dict()

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

    def clone_session(self, owner):
        self.input.put({'op': 'clone'})
        session = Session(self.output.get().get('new-session'))
        self.sessions_by_id[session.id] = session
        self.sessions_by_owner[owner] = session

        log.debug({
            'event': 'new-session/plugin',
            'id': session.id
        })

        return session

    def describe(self):
        self.input.put({
            'op': 'describe',
            'session': self.sessions_by_owner['plugin'].id
        })

    def go(self):
        eval_loop = Thread(daemon=True, target=self.eval_loop)
        eval_loop.name = 'tutkain.client.eval_loop'
        eval_loop.start()

        read_loop = Thread(daemon=True, target=self.read_loop)
        read_loop.name = 'tutkain.client.read_loop'
        read_loop.start()

        self.clone_session('plugin')
        self.clone_session('user')

    def eval(self, code, owner='user', handler=None):
        session = self.sessions_by_owner[owner]
        op = session.mkop({'op': 'eval', 'code': code})

        if not handler:
            handler = self.output.put

        session.handlers[op['id']] = handler

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

    def handle(self, response):
        session_id = response.get('session')
        item_id = response.get('id')
        session = self.sessions_by_id.get(session_id)

        if session:
            handler = session.handlers.get(item_id, self.output.put)
        else:
            handler = self.output.put

        try:
            handler.__call__(response)
        finally:
            if session and response.get('status') == ['done']:
                session.handlers.pop(item_id, None)
                session.errors.pop(item_id, None)

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
