import socket
from threading import Event, Thread

from unittest import TestCase
from Tutkain.lib.repl import bencode


def echo_loop(server, stop_event):
    conn, _ = server.accept()

    while not stop_event.is_set():
        data = conn.recv(1024)
        conn.sendall(data)


def start_server(stop_event):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 0))
    server.listen(1)

    serve_loop = Thread(
        daemon=True,
        target=echo_loop,
        args=(server, stop_event,)
    )

    serve_loop.name = 'tutkain.test.serve_loop'
    serve_loop.start()
    return server


class TestBencode(TestCase):
    @classmethod
    def setUpClass(self):
        self.stop_event = Event()
        self.server = start_server(self.stop_event)
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(self.server.getsockname())
        self.client.settimeout(0.5)

    @classmethod
    def tearDownClass(self):
        if self.client:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()

        if self.server:
            self.stop_event.set()

    def setUp(self):
        self.buffer = self.client.makefile(mode='rwb')

    def test_roundtrip(self):
        for val in [
            42,
            0,
            -42,
            'Hello, world!',
            'äö',
            ['spam', 42],
            {'foo': 42, 'bar': 'spam'},
            ['cheese', 42, {'ham': 'eggs'}],
            {'cheese': 42, 'ham': ['eggs']}
        ]:
            bencode.write(self.buffer, val)
            self.assertEquals(val, bencode.read(self.buffer))

    def test_invalid_byte_string(self):
        self.client.sendall(b'4spam')
        # TODO: What would be a sensible failure mode?
        self.assertRaises(socket.timeout, bencode.read, self.buffer)
