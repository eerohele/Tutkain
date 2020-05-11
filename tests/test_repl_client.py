from unittest import TestCase

from tutkain import repl_client


# NOTE: Before you run these tests, you must start an nREPL server at
# localhost:1234:
#
#     $ cd tests/fixtures
#     $ clojure -m nrepl.cmdline --port 1234
class TestReplClient(TestCase):
    def test_repl_client(self):
        with repl_client.ReplClient('localhost', 1234) as repl:
            versions = repl.output.get().get('versions')
            nrepl_version = versions.get('nrepl').get('version-string')
            clojure_version = versions.get('clojure').get('version-string')

            self.assertEquals(nrepl_version, '0.7.0')
            self.assertEquals(clojure_version, '1.10.1')

            repl.input.put(
                repl.user_session.eval_op({
                    'code': '(+ 1 2 3)'
                })
            )

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
            repl.user_session = None
            self.assertIsNone(repl_client.get(1))
