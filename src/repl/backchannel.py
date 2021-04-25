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

    def __init__(self, host, port):
        self.stop_event = Event()
        self.host = host
        self.port = port
        self.sendq = queue.Queue()
        self.recvq = queue.Queue()
        self.handlers = {}
        self.message_id = itertools.count(1)
        self.options = {}

    def augment(self, item):
        if item.get(edn.Keyword("dialect")) == edn.Keyword("cljs") and "shadow-build-id" in self.options:
            item[edn.Keyword("build-id")] = self.options["shadow-build-id"]

    def send_loop(self):
        try:
            while item := self.sendq.get():
                self.augment(item)
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
        op[mid] = next(self.message_id)

        if handler:
            self.handlers[op[mid]] = handler

        self.sendq.put(op)

    def handle(self, response):
        id = response.get(edn.Keyword("id"))

        try:
            handler = self.handlers.get(id, self.recvq.put)
            handler.__call__(response)
        finally:
            self.handlers.pop(id, None)

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