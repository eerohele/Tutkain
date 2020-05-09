import socket
from threading import Event, Thread

from unittest import TestCase
import tutkain.bencode as bencode


def serve_loop(server, stop_event):
    conn, _ = server.accept()

    while not stop_event.wait(0):
        data = conn.recv(1024)
        conn.sendall(data)


def start_server(stop_event):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(('localhost', 0))
    server.listen(1)
    Thread(daemon=True, target=serve_loop, args=(server, stop_event,)).start()
    return server


class TestBencode(TestCase):
    server = None
    client = None
    stop_event = None

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
            self.client.close()
            self.client = None

        if self.server:
            self.stop_event.set()
            self.stop_event = None
            self.server = None

    def test_read_int(self):
        self.client.sendall(b'i42e')
        self.assertEquals(bencode.read(self.client), 42)
        self.client.sendall(b'i0e')
        self.assertEquals(bencode.read(self.client), 0)
        self.client.sendall(b'i-42e')
        self.assertEquals(bencode.read(self.client), -42)

    def test_read_byte_string(self):
        self.client.sendall(b'4:spam')
        self.assertEquals(bencode.read(self.client), 'spam')

    def test_read_non_ascii_byte_string(self):
        self.client.sendall(b'4:\xc3\xa4\xc3\xb6')
        self.assertEquals(bencode.read(self.client), 'äö')

    def test_read_list(self):
        self.client.sendall(b'l4:spami42ee')
        self.assertEquals(bencode.read(self.client), ['spam', 42])

    def test_read_dict(self):
        self.client.sendall(b'd3:bar4:spam3:fooi42ee')
        self.assertEquals(
            bencode.read(self.client),
            {'foo': 42, 'bar': 'spam'}
        )

    def test_read_invalid_byte_string(self):
        self.client.sendall(b'4spam')
        self.assertRaises(socket.timeout, bencode.read, self.client)

    def test_write_str(self):
        self.assertEquals(
            bencode.write('Hello, world!'),
            b'13:Hello, world!'
        )

    def test_write_non_ascii_str(self):
        self.assertEquals(
            bencode.write('äö'),
            b'4:\xc3\xa4\xc3\xb6'
        )

    def test_write_int(self):
        self.assertEquals(
            bencode.write(42),
            b'i42e'
        )

    def test_write_list(self):
        self.assertEquals(
            bencode.write(['spam', 42]),
            b'l4:spami42ee'
        )

    def test_write_dict(self):
        self.assertEquals(
            bencode.write({'foo': 42, 'bar': 'spam'}),
            b'd3:bar4:spam3:fooi42ee'
        )
