import queue
import socket
import uuid
from threading import Thread, Event

from . import bencode
from ..log import log


class Client(object):
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.buffer = self.socket.makefile(mode="rwb")

        log.debug({"event": "socket/connect", "host": self.host, "port": self.port})

        return self

    def disconnect(self):
        if self.socket is not None:
            try:
                self.buffer.close()
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                log.debug({"event": "socket/disconnect"})
            except OSError as e:
                log.debug({"event": "error", "exception": e})

    def __init__(self, host, port):
        self.uuid = str(uuid.uuid4())
        self.host = host
        self.port = port
        self.sendq = queue.Queue()
        self.recvq = queue.Queue()
        self.stop_event = Event()
        self.sessions = {}
        self.sessions_by_owner = {}
        self.handlers = {}

    def id(self):
        return self.uuid

    def register_session(self, owner, session):
        self.sessions[session.id] = session
        self.sessions_by_owner[owner] = session
        return session

    def go(self):
        self.connect()

        send_loop = Thread(daemon=True, target=self.send_loop)
        send_loop.name = "tutkain.client.send_loop"
        send_loop.start()

        recv_loop = Thread(daemon=True, target=self.recv_loop)
        recv_loop.name = "tutkain.client.recv_loop"
        recv_loop.start()

        return self

    def __enter__(self):
        self.go()
        return self

    def send_loop(self):
        while True:
            item = self.sendq.get()

            if item is None:
                break

            log.debug({"event": "socket/send", "item": item})

            bencode.write(self.buffer, item)

        log.debug({"event": "thread/exit"})

    def send(self, op, handler=None):
        id = str(uuid.uuid4())
        op["id"] = id
        self.handlers[id] = handler
        self.sendq.put(op)

    def handle(self, response):
        id = response.get("id")
        session_id = response.get("session")
        session = self.sessions.get(session_id)

        if session:
            session.handle(response)
        else:
            try:
                handler = self.handlers.get(id, self.recvq.put)
                handler.__call__(response)
            finally:
                self.handlers.pop(id, None)

    def recv_loop(self):
        try:
            while not self.stop_event.is_set():
                item = bencode.read(self.buffer)

                if item is None:
                    self.recvq.put({"value": ":tutkain/disconnected"})
                    break

                log.debug({"event": "socket/recv", "item": item})

                self.handle(item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            # If we receive a stop event, put a None into the queue to tell
            # consumers to stop reading it.
            self.recvq.put(None)

            # Feed poison pill to input queue.
            self.sendq.put(None)

            log.debug({"event": "thread/exit"})

            # We've exited the loop that reads from the socket, so we can
            # close the connection to the socket.
            self.disconnect()

    def close_session(self, owner, handler=lambda _: None):
        sessions = self.sessions_by_owner

        if sessions and owner in sessions:
            session = sessions[owner]

            if session.supports("close"):
                session.send({"op": "close"}, handler=handler)

    def halt(self):
        log.debug({"event": "client/halt"})

        if self.sessions_by_owner:
            self.close_session("user")
            self.close_session("plugin")

            self.close_session(
                "sideloader",
                handler=lambda response: "status" in response
                and "done" in response["status"]
                and self.stop_event.set(),
            )
        else:
            self.stop_event.set()

    def __exit__(self, type, value, traceback):
        self.halt()
