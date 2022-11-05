from unittest import TestCase

import sublime

from Tutkain.api import edn
from Tutkain.src.repl import ports


class TestPorts(TestCase):
    def setUp(self):
        sublime.run_command("new_window")
        self.window = sublime.active_window()

    def tearDown(self):
        if window := self.window:
            window.run_command("close_window")

    def test_parse_port(self):
        # Parsing port from string to int
        self.assertEquals(
            1234, ports.parse(self.window, "1234", edn.Keyword("clj"), lambda *_: [])
        )

        # Pass "auto" -> use discovered port
        self.assertEquals(
            1234,
            ports.parse(
                self.window, "auto", edn.Keyword("clj"), lambda *_: [("", "1234")]
            ),
        )
