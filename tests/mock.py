import socket
import queue
from concurrent import futures

from Tutkain.api import edn


def send_text(buffer, message):
    buffer.write(message)
    buffer.write("\n")
    buffer.flush()


def send_edn(buffer, message):
    edn.write(buffer, message)


class Server(object):
    def __init__(self, send_fn, port=0, greeting=lambda _: None, timeout=1):
        self.send_fn = send_fn
        self.conn = None
        self.executor = futures.ThreadPoolExecutor()
        self.greeting = greeting
        self.port = port
        self.timeout = timeout
        self.recvq = queue.Queue()

    def recv_loop(self):
        while item := self.buffer().readline():
            self.recvq.put(item)

    def recv(self, timeout=1):
        return self.recvq.get(timeout=timeout)

    def send(self, message):
        self.send_fn(self.buffer(), message)

    def wait(self):
        self.conn, _ = self.socket.accept()
        buffer = self.conn.makefile(mode="rw")
        self.greeting(buffer)
        return buffer

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(("localhost", self.port))
        self.socket.listen()
        self.socket.settimeout(self.timeout)
        self.buf = self.executor.submit(self.wait)
        self.host, self.port = self.socket.getsockname()
        self.executor.submit(self.recv_loop)
        return self

    def __enter__(self):
        return self.executor.submit(self.start).result(timeout=self.timeout)

    def buffer(self):
        return self.buf.result(timeout=self.timeout)

    def stop(self):
        self.executor.shutdown(wait=False)

    def __exit__(self, type, value, traceback):
        self.stop()
