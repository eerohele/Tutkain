from unittest import TestCase
from .util import start_client, stop_client, start_server

from Tutkain.api import edn


class TestEdn(TestCase):
    @classmethod
    def setUpClass(self):
        self.server, self.stop_event = start_server()
        self.client = start_client(self.server)

    @classmethod
    def tearDownClass(self):
        self.stop_event.set()
        stop_client(self.client)

    def setUp(self):
        self.buffer = self.client.makefile(mode="rw")

    def test_roundtrip(self):
        for val in [
            None,
            True,
            False,
            42,
            0,
            # -42,
            "Hello, world!",
            "foo \"bar\" baz",
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
            {edn.Keyword("a"): [{edn.Keyword("b"): edn.Keyword("c")}]}
        ]:
            edn.write(self.buffer, val)
            self.assertEquals(val, edn.read_line(self.buffer))
