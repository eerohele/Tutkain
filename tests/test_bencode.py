import socket
from unittest import TestCase
from Tutkain.src.repl import bencode
from .util import start_client, stop_client, start_server


class TestBencode(TestCase):
    @classmethod
    def setUpClass(self):
        self.server, self.stop_event = start_server()
        self.client = start_client(self.server)

    @classmethod
    def tearDownClass(self):
        self.stop_event.set()
        stop_client(self.client)

    def setUp(self):
        self.buffer = self.client.makefile(mode="rwb")

    def test_roundtrip(self):
        for val in [
            42,
            0,
            -42,
            "Hello, world!",
            "äö",
            ["spam", 42],
            {"foo": 42, "bar": "spam"},
            ["cheese", 42, {"ham": "eggs"}],
            {"cheese": 42, "ham": ["eggs"]},
        ]:
            bencode.write(self.buffer, val)
            self.assertEquals(val, bencode.read(self.buffer))

    def test_invalid_byte_string(self):
        self.client.sendall(b"4spam")
        # TODO: What would be a sensible failure mode?
        self.assertRaises(socket.timeout, bencode.read, self.buffer)
