import socket

from concurrent import futures
from Tutkain.src.repl import bencode


class Server:
    """A mock nREPL server.

    Use recv() to receive Bencoded data from the client. Use send() to send bencoded data to the
    client.
    """

    def __init__(self):
        self.server = self.socket_server()
        self.executor = futures.ThreadPoolExecutor(max_workers=1)
        self.host, self.port = self.server.getsockname()
        self.future = self.executor.submit(self.buffer)

    def buffer(self):
        connection, _ = self.server.accept()
        return connection.makefile(mode="rwb")

    def socket_server(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("localhost", 0))
        server.listen(1)
        server.settimeout(1)
        return server

    def send(self, x):
        bencode.write(self.future.result(timeout=1), x)

    def recv(self):
        return bencode.read(self.future.result(timeout=1))

    def shutdown(self):
        self.executor.shutdown(wait=False)
