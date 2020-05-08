import socket

from unittest import TestCase
import tutkain.bencode as bencode


# NOTE: Before you run these tests, you must start a TCP echo server at
# localhost:4321:
#
#     $ ncat -l 4321 --keep-open --sh-exec cat
class TestBencode(TestCase):
    server = None
    client = None

    def setUp(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(('localhost', 4321))

    def tearDown(self):
        if self.client is not None:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()

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
