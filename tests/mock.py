from abc import ABC, abstractmethod
import io
import socket
import queue
from concurrent import futures

from Tutkain.api import edn


class Server(ABC):
    def __init__(self, port=0, greeting=lambda _: None, timeout=1):
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

    @abstractmethod
    def send(self, message):
        pass

    def wait(self):
        self.conn, _ = self.socket.accept()
        buffer = self.conn.makefile(mode="rw", buffering=io.DEFAULT_BUFFER_SIZE)
        self.greeting(buffer)
        return buffer

    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
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
        self.socket.close()
        self.executor.shutdown(wait=False)

    def __exit__(self, type, value, traceback):
        self.stop()


class REPL(Server):
    def send(self, message):
        self.buffer().write(message + "\n")
        self.buffer().flush()


class Backchannel(Server):
    def send(self, message):
        edn.write_line(self.buffer(), message)
