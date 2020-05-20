from unittest import TestCase

from tutkain.repl import Client
from tutkain import sessions


# NOTE: Before you run these tests, you must start an nREPL server at
# localhost:1234:
#
#     $ cd tests/fixtures
#     $ clojure -A:nrepl/server
class TestClient(TestCase):
    @classmethod
    def setUpClass(self):
        sessions.wipe()

    @classmethod
    def tearDownClass(self):
        sessions.wipe()

    def test_client(self):
        with Client('localhost', 1234) as client:
            client.input.put({'op': 'eval', 'code': '(+ 1 2 3)'})
            self.assertEquals(client.output.get().get('value'), '6')

    def test_client_session(self):
        with Client('localhost', 1234) as client:
            session = client.clone_session()
            session.send({'op': 'eval', 'code': '(+ 1 2 3)'})
            self.assertEquals(client.output.get().get('value'), '6')

    def test_session_registry(self):
        with Client('localhost', 1234) as client:
            session = client.clone_session()
            sessions.register(1, 'user', session)
            self.assertEquals(sessions.get_by_id(session.id), session)
            self.assertEquals(sessions.get_by_owner(1, 'user'), session)
            sessions.deregister(1)
            self.assertEquals(sessions.get_by_id(session.id), None)
            self.assertEquals(sessions.get_by_owner(1, 'user'), None)

    def test_session_registry_wipe(self):
        with Client('localhost', 1234) as client:
            session = client.clone_session()
            sessions.register(1, 'user', session)
            self.assertEquals(sessions.get_by_id(session.id), session)
            self.assertEquals(sessions.get_by_owner(1, 'user'), session)
            sessions.wipe()
            self.assertEquals(sessions.get_by_id(session.id), None)
            self.assertEquals(sessions.get_by_owner(1, 'user'), None)
