import sublime
import sys
import os
import time

from unittest import TestCase

sys.path.append(os.path.join(os.path.dirname(__file__), 'dependencies'))

import edn_format
from edn_format import Keyword

Tutkain = sys.modules["Tutkain.tutkain"]


class TestReplClient(TestCase):
    def test_repl_client(self):
        # You have to start a socket REPL on localhost:12345 to run this test.
        with Tutkain.ReplClient('localhost', 12345) as repl_client:
            repl_client.input.put('(+ 1 2 3)')
            self.assertEquals(repl_client.output.get().get(Keyword('val')), '6')
