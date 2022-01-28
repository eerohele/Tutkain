"""Unit tests for the EDN module."""

from unittest import TestCase
from Tutkain.api import edn
from .util import start_client, stop_client, start_server


class TestEdn(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server, cls.stop_event = start_server()
        cls.client = start_client(cls.server)

    @classmethod
    def tearDownClass(cls):
        cls.stop_event.set()
        stop_client(cls.client)

    def setUp(self):
        self.buffer = self.client.makefile(mode="rw")

    def test_character(self):
        self.buffer.write("\\newline")
        self.buffer.flush()
        self.assertEqual("\n", edn.read(self.buffer.read(8)))

    def test_roundtrip(self):
        for val in [
            None,
            True,
            False,
            42,
            0,
            # -42,
            "Hello, world!",
            "foo \"bar\" quux\\n",
            "äö",
            [],
            ["spam", 42, 84],
            set([1, 2, 3]),
            edn.Keyword("foo"),
            edn.Keyword("bar", "foo"),
            {"foo": 42, "bar": "spam"},
            ["cheese", 42, {"ham": "eggs"}],
            {"cheese": 42, "ham": ["eggs"]},
            {"status": ["error", "namespace-not-found", "done"], "id": 11},
            {"a": []},
            {"a": [{"b": "c"}]},
            {edn.Keyword("a"): [{edn.Keyword("b"): edn.Keyword("c")}]},
            {},
        ]:
            edn.write_line(self.buffer, val)
            self.assertEqual(val, edn.read_line(self.buffer))
