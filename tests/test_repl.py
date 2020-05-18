from unittest import TestCase

from tutkain.repl import Client, ClientRegistry


# NOTE: Before you run these tests, you must start an nREPL server at
# localhost:1234:
#
#     $ cd tests/fixtures
#     $ clojure -A:nrepl/server
class TestClient(TestCase):
    @classmethod
    def setUpClass(self):
        ClientRegistry.deregister_all()

    @classmethod
    def tearDownClass(self):
        ClientRegistry.deregister_all()

    def test_client(self):
        with Client('localhost', 1234) as client:
            client.eval('(+ 1 2 3)')
            self.assertEquals(client.output.get().get('value'), '6')

    def test_client_registry_deregister(self):
        with Client('localhost', 1234) as client:
            ClientRegistry.register(1, client)
            self.assertEquals(ClientRegistry.get_all(), {1: client})
            ClientRegistry.deregister(1)
            self.assertEquals(ClientRegistry.get_all(), {})

    def test_client_get(self):
        with Client('localhost', 1234) as client:
            ClientRegistry.register(1, client)
            self.assertEquals(ClientRegistry.get(1), client)
            ClientRegistry.deregister(1)
            self.assertIsNone(ClientRegistry.get(1))
