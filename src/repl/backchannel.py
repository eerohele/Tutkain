import itertools
import queue
import socket

from threading import Event, Thread

from ...api import edn
from ..log import log


class Backchannel(object):
    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.buffer = self.socket.makefile(mode="rw")

        log.debug({"event": "backchannel/connect", "host": self.host, "port": self.port})

        send_loop = Thread(daemon=True, target=self.send_loop)
        send_loop.name = "tutkain.backchannel.send_loop"
        send_loop.start()

        recv_loop = Thread(daemon=True, target=self.recv_loop)
        recv_loop.name = "tutkain.backchannel.recv_loop"
        recv_loop.start()

        return self

    def disconnect(self):
        if self.socket is not None:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
                self.socket.close()
                log.debug({"event": "backchannel/disconnect"})
            except OSError as e:
                log.debug({"event": "error", "exception": e})

    def __init__(self, client, host, port):
        self.stop_event = Event()
        self.client = client
        self.host = host
        self.port = port
        self.sendq = queue.Queue()
        self.handlers = {}
        self.message_id = itertools.count(1)

    def send_loop(self):
        try:
            while item := self.sendq.get():
                log.debug({"event": "backchannel/send", "item": item})
                edn.write(self.buffer, item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            self.disconnect()
            self.stop_event.set()
            log.debug({"event": "thread/exit"})

    def send(self, op, handler=None):
        mid = edn.Keyword("id")
        op = edn.kwmap(op)
        op[mid] = next(self.message_id)

        if handler:
            self.handlers[op[mid]] = handler

        self.sendq.put(op)

    def handle(self, response):
        try:
            if not isinstance(response, dict):
                self.client.recvq.put(response)
            # It's an exception but the client doesn't want to handle it.
            elif response.get(edn.Keyword("exception")) and not response.get(edn.Keyword("handle-exception")):
                self.client.recvq.put(response)
            elif response.get(edn.Keyword("debug")):
                log.debug({"event": "info", "message": response.get(edn.Keyword("val"))})
            else:
                id = response.get(edn.Keyword("id"))

                try:
                    handler = self.handlers.get(id)
                    handler.__call__(response)
                finally:
                    self.handlers.pop(id, None)
        except AttributeError as error:
            log.error({"event": "error", "response": response, "error": error})

    def recv_loop(self):
        try:
            while not self.stop_event.is_set() and (item := edn.read_line(self.buffer)):
                log.debug({"event": "backchannel/recv", "item": item})
                self.handle(item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            log.debug({"event": "thread/exit"})

    def halt(self):
        log.debug({"event": "backchannel/halt"})
        self.sendq.put(None)


class NoopBackchannel():
    def send(self, op, handler=None):
        pass

    def halt(self):
        pass
