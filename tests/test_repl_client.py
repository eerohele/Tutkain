from unittest import TestCase

from tutkain import repl_client


# NOTE: Before you run these tests, you must start an nREPL server at
# localhost:1234:
#
#     $ cd tests/fixtures
#     $ clojure -A:nrepl/server
class TestReplClient(TestCase):
    @classmethod
    def setUpClass(self):
        repl_client.deregister_all()

    @classmethod
    def tearDownClass(self):
        repl_client.deregister_all()

    def test_repl_client(self):
        with repl_client.ReplClient('localhost', 1234) as repl:
            repl.eval('(+ 1 2 3)')
            self.assertEquals(repl.output.get().get('value'), '6')

    def test_repl_client_register_deregister(self):
        with repl_client.ReplClient('localhost', 1234) as repl:
            repl_client.register(1, repl)
            self.assertEquals(repl_client.get_all(), {1: repl})
            repl_client.deregister(1)
            self.assertEquals(repl_client.get_all(), {})

    def test_repl_client_get(self):
        with repl_client.ReplClient('localhost', 1234) as repl:
            repl_client.register(1, repl)
            self.assertEquals(repl_client.get(1), repl)
            repl_client.deregister(1)
            self.assertIsNone(repl_client.get(1))
