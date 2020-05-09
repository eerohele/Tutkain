from unittest import TestCase

from tutkain.repl_client import ReplClient


# NOTE: Before you run these tests, you must start an nREPL server at
# localhost:1234:
#
#     $ cd tests/fixtures
#     $ clojure -m nrepl.cmdline --port 1234
class TestReplClient(TestCase):
    def test_repl_client(self):
        with ReplClient('localhost', 1234) as repl_client:
            versions = repl_client.output.get().get('versions')
            nrepl_version = versions.get('nrepl').get('version-string')
            clojure_version = versions.get('clojure').get('version-string')

            self.assertEquals(nrepl_version, '0.7.0')
            self.assertEquals(clojure_version, '1.10.1')

            repl_client.input.put(
                repl_client.user_session.eval_op({
                    'code': '(+ 1 2 3)'
                })
            )

            self.assertEquals(repl_client.output.get().get('value'), '6')
