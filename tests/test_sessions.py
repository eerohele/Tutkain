from unittest import TestCase

from tutkain.session import Session
from tutkain import sessions


class MockClient(object):
    def halt(self):
        pass


class TestClient(TestCase):
    @classmethod
    def setUpClass(self):
        sessions.wipe()

    @classmethod
    def tearDownClass(self):
        sessions.wipe()

    def test_session_registry(self):
        client = MockClient()
        session = Session('1FC66CB0-1131-4B9D-AF4D-D071826D2873', client)
        sessions.register(1, 'user', session)
        self.assertEquals(sessions.get_by_id(session.id), session)
        self.assertEquals(sessions.get_by_owner(1, 'user'), session)
        sessions.deregister(1)
        self.assertEquals(sessions.get_by_id(session.id), None)
        self.assertEquals(sessions.get_by_owner(1, 'user'), None)

    def test_session_registry_wipe(self):
        client = MockClient()
        session = Session('1FC66CB0-1131-4B9D-AF4D-D071826D2873', client)
        sessions.register(1, 'user', session)
        self.assertEquals(sessions.get_by_id(session.id), session)
        self.assertEquals(sessions.get_by_owner(1, 'user'), session)
        sessions.wipe()
        self.assertEquals(sessions.get_by_id(session.id), None)
        self.assertEquals(sessions.get_by_owner(1, 'user'), None)
