import sublime
import uuid

from inspect import cleandoc
from . import mock
from .util import TestRepl, ViewTestCase
from Tutkain.src import state
from Tutkain.src import test
from Tutkain.src.repl import b64encode_file


ROOT = sublime.packages_path()


def send_eval_responses(server, session_id, id, ns, value):
    server.send({"id": id, "session": session_id, "value": value})
    server.send({"id": id, "ns": ns, "session": session_id})
    server.send({"id": id, "session": session_id, "status": ["done"]})


def select_keys(d, ks):
    return {k: d[k] for k in ks}


class TestBabashka(ViewTestCase):
    capabilities = {
        "ops": {
            "clone": {},
            "close": {},
            "complete": {},
            "describe": {},
            "eldoc": {},
            "eval": {},
            "load-file": {},
            "ls-sessions": {},
        },
        "session": "none",
        "status": ["done"],
        "versions": {"babashka": "0.2.2", "babashka.nrepl": "0.0.4-SNAPSHOT"},
    }

    def test_handshake(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()

            # Client sends describe op
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("describe", msg["op"])

            # Server sends describe reply
            self.capabilities["id"] = msg["id"]
            server.send(self.capabilities)

            # Client initializes plugin session
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            plugin_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": plugin_session_id,
                    "session": "none",
                    "status": ["done"],
                }
            )

            # Client initializes user session
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            user_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": user_session_id,
                    "session": "none",
                    "status": ["done"],
                }
            )

            self.assertEquals(
                "Babashka 0.2.2\nbabashka.nrepl 0.0.4-SNAPSHOT\n", repl.take_print()
            )

            return server, repl, plugin_session_id, user_session_id
        finally:
            server.shutdown()

    def make_sessions(self, server, repl):
        self.capabilities["id"] = server.recv()["id"]
        server.send(self.capabilities)

        plugin_session_id = str(uuid.uuid4())

        server.send(
            {
                "id": server.recv()["id"],
                "new-session": plugin_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        user_session_id = str(uuid.uuid4())

        server.send(
            {
                "id": server.recv()["id"],
                "new-session": user_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        repl.take_print()

        return plugin_session_id, user_session_id

    def test_evaluate_form(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            # Client evaluates (inc 1)
            self.set_view_content("(inc 1)")
            self.set_selections((0, 0))
            self.view.run_command("tutkain_evaluate_form")

            # # Server receives eval op
            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(inc 1)",
                    "ns": "user",
                    "session": user_session_id,
                    "id": 1,
                },
                select_keys(server.recv(), {"op", "code", "ns", "session", "id"}),
            )

            # Server sends eval responses
            server.send(
                {
                    "id": 1,
                    "ns": "user",
                    "session": user_session_id,
                    "value": "2",
                }
            )

            server.send({"id": 1, "ns": "user", "session": user_session_id})

            server.send(
                {
                    "id": 1,
                    "session": user_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals("user=> (inc 1)\n", repl.take_print())
            self.assertEquals("2", repl.take_print())
            self.assertEquals("\n", repl.take_print())
        finally:
            server.shutdown()


class TestArcadia(ViewTestCase):
    capabilities = {
        "ops": {
            "classpath": 1,
            "clone": 1,
            "complete": 1,
            "describe": 1,
            "eldoc": 1,
            "eval": 1,
            "info": 1,
            "load-file": 1,
        },
        "session": str(uuid.uuid4()),
        "status": ["done"],
        "versions": {
            "clojure": {
                "incremental": 0,
                "major": 1,
                "minor": 10,
                "qualifier": "master",
            },
            "nrepl": {"incremental": 3, "major": 0, "minor": 2},
        },
    }

    def test_handshake(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()

            # Client sends describe op
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("describe", msg["op"])

            self.capabilities["id"] = msg["id"]

            # Server sends describe reply
            server.send(self.capabilities)

            # Client initializes plugin session
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            plugin_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": plugin_session_id,
                    "status": ["done"],
                }
            )

            # Client initializes user session
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            user_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": user_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals("Clojure 1.10.0\nnREPL 0.2.3\n", repl.take_print())
        finally:
            server.shutdown()

    def make_sessions(self, server, repl):
        self.capabilities["id"] = server.recv()["id"]
        server.send(self.capabilities)

        plugin_session_id = str(uuid.uuid4())

        server.send(
            {
                "id": server.recv()["id"],
                "new-session": plugin_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        user_session_id = str(uuid.uuid4())

        server.send(
            {
                "id": server.recv()["id"],
                "new-session": user_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        repl.take_print()

        return plugin_session_id, user_session_id

    def test_evaluate_form(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            # Client evaluates (inc 1)
            self.set_view_content("(inc 1)")
            self.set_selections((0, 0))
            self.view.run_command("tutkain_evaluate_form")

            # # Server receives eval op
            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(inc 1)",
                    "ns": "user",
                    "session": user_session_id,
                    "id": 1,
                },
                select_keys(server.recv(), {"op", "code", "ns", "session", "id"}),
            )

            # Server sends eval responses
            server.send(
                {
                    "id": 1,
                    "ns": "user",
                    "session": user_session_id,
                    "value": "2",
                }
            )

            server.send({"id": 1, "ns": "user", "session": user_session_id})

            server.send(
                {
                    "id": 1,
                    "session": user_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals("user=> (inc 1)\n", repl.take_print())
            self.assertEquals("2", repl.take_print())
            self.assertEquals("\n", repl.take_print())
        finally:
            server.shutdown()


class TestDefault(ViewTestCase):
    capabilities = {
        "aux": {"current-ns": "user"},
        "ops": {
            "add-middleware": {},
            "clone": {},
            "close": {},
            "completions": {},
            "describe": {},
            "eval": {},
            "interrupt": {},
            "load-file": {},
            "lookup": {},
            "ls-middleware": {},
            "ls-sessions": {},
            "sideloader-provide": {},
            "sideloader-start": {},
            "stdin": {},
            "swap-middleware": {},
            "tutkain/add-tap": {},
            "tutkain/test": {},
        },
        "status": ["done"],
        "versions": {
            "clojure": {
                "incremental": 1,
                "major": 1,
                "minor": 10,
                "version-string": "1.10.1",
            },
            "java": {
                "incremental": "2",
                "major": "11",
                "minor": "0",
                "version-string": "11.0.2",
            },
            "nrepl": {
                "incremental": 3,
                "major": 0,
                "minor": 8,
                "version-string": "0.8.3",
            },
        },
    }

    def test_sideloading_handshake(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()

            # Client sends describe op.
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("describe", msg["op"])

            # Server sends describe reply.
            server.send(
                {
                    "aux": {"current-ns": "user"},
                    "id": msg["id"],
                    "ops": {
                        "add-middleware": {},
                        "clone": {},
                        "close": {},
                        "completions": {},
                        "describe": {},
                        "eval": {},
                        "interrupt": {},
                        "load-file": {},
                        "lookup": {},
                        "ls-middleware": {},
                        "ls-sessions": {},
                        "sideloader-provide": {},
                        "sideloader-start": {},
                        "stdin": {},
                        "swap-middleware": {},
                    },
                    "session": str(uuid.uuid4()),
                    "status": ["done"],
                    "versions": {
                        "clojure": {
                            "incremental": 1,
                            "major": 1,
                            "minor": 10,
                            "version-string": "1.10.1",
                        },
                        "java": {
                            "incremental": "2",
                            "major": "11",
                            "minor": "0",
                            "version-string": "11.0.2",
                        },
                        "nrepl": {
                            "incremental": 3,
                            "major": 0,
                            "minor": 8,
                            "version-string": "0.8.3",
                        },
                    },
                }
            )

            # Client initializes sideloader session.
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            sideloader_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            # Client sends sideloader-start.
            self.assertEquals(
                {
                    "id": 1,
                    "op": "sideloader-start",
                    "session": sideloader_session_id,
                },
                server.recv(),
            )

            # Client requires pprint namespace.
            self.assertEquals(
                {
                    "op": "eval",
                    "id": 2,
                    "code": "(require 'tutkain.nrepl.util.pprint)",
                    "session": sideloader_session_id,
                },
                select_keys(server.recv(), {"op", "id", "code", "session"}),
            )

            # Server can't find the pprint namespace, requests it from the client.
            server.send(
                {
                    "id": 1,
                    "name": "tutkain/nrepl/util/pprint__init.class",
                    "session": sideloader_session_id,
                    "status": ["sideloader-lookup"],
                    "type": "resource",
                }
            )

            # Client doesn't have the .class file, sends an empty response.
            self.assertEquals(
                {
                    "id": 3,
                    "op": "sideloader-provide",
                    "type": "resource",
                    "name": "tutkain/nrepl/util/pprint__init.class",
                    "content": "",
                    "session": sideloader_session_id,
                },
                server.recv(),
            )

            # Server acknowledges the empty response.
            server.send(
                {
                    "id": 3,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            # Server requests a .clj file.
            server.send(
                {
                    "id": 1,
                    "name": "tutkain/nrepl/util/pprint.clj",
                    "session": sideloader_session_id,
                    "status": ["sideloader-lookup"],
                    "type": "resource",
                }
            )

            # Client has it, sends it.
            self.assertEquals(
                {
                    "id": 4,
                    "op": "sideloader-provide",
                    "type": "resource",
                    "name": "tutkain/nrepl/util/pprint.clj",
                    "content": b64encode_file(
                        f"{ROOT}/Tutkain/clojure/src/tutkain/nrepl/util/pprint.clj"
                    ),
                    "session": sideloader_session_id,
                },
                server.recv(),
            )

            # Server acknoledges the provide.
            server.send(
                {
                    "id": 4,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            # The request that required the pprint namespace is done.
            #
            # We'll ignore sideloading Fipp here.
            server.send({"id": 2, "session": sideloader_session_id, "value": "nil"})
            server.send({"id": 2, "ns": "user", "session": sideloader_session_id})
            server.send({"id": 2, "session": sideloader_session_id, "status": ["done"]})

            # Client asks server to add middleware.
            self.assertEquals(
                {
                    "op": "add-middleware",
                    "middleware": [
                        "tutkain.nrepl.middleware.test/wrap-test",
                        "tutkain.nrepl.middleware.tap/wrap-tap",
                    ],
                    "session": sideloader_session_id,
                    "id": 5,
                },
                server.recv(),
            )

            # Server doesn't have the middleware, asks the client for it.
            server.send(
                {
                    "id": 1,
                    "name": "tutkain/nrepl/middleware/test__init.class",
                    "session": sideloader_session_id,
                    "status": ["sideloader-lookup"],
                    "type": "resource",
                }
            )

            # Client doesn't have the .class file, sends an empty response.
            self.assertEquals(
                {
                    "id": 6,
                    "op": "sideloader-provide",
                    "type": "resource",
                    "name": "tutkain/nrepl/middleware/test__init.class",
                    "content": "",
                    "session": sideloader_session_id,
                },
                server.recv(),
            )

            # Server asks the client for the .clj file.
            server.send(
                {
                    "id": 1,
                    "name": "tutkain/nrepl/middleware/test.clj",
                    "session": sideloader_session_id,
                    "status": ["sideloader-lookup"],
                    "type": "resource",
                }
            )

            # Client has the class file, sends it to the server
            self.assertEquals(
                {
                    "id": 7,
                    "op": "sideloader-provide",
                    "type": "resource",
                    "name": "tutkain/nrepl/middleware/test.clj",
                    "content": b64encode_file(
                        f"{ROOT}/Tutkain/clojure/src/tutkain/nrepl/middleware/test.clj"
                    ),
                    "session": sideloader_session_id,
                },
                server.recv(),
            )

            # Server acknoledges the provide.
            server.send(
                {
                    "id": 7,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            # Server tells the client there's nothing more to sideload.
            server.send(
                {
                    "id": 5,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            # Client sends tutkain/add-tap.
            self.assertEquals(
                {"id": 8, "op": "tutkain/add-tap", "session": sideloader_session_id},
                server.recv(),
            )

            # Server acknowledges the request.
            server.send(
                {
                    "id": 8,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                {"id": 9, "op": "describe", "session": sideloader_session_id},
                server.recv(),
            )

            server.send(
                {
                    "aux": {"current-ns": "user"},
                    "id": 9,
                    "ops": {
                        "add-middleware": {},
                        "clone": {},
                        "close": {},
                        "completions": {},
                        "describe": {},
                        "eval": {},
                        "interrupt": {},
                        "load-file": {},
                        "lookup": {},
                        "ls-middleware": {},
                        "ls-sessions": {},
                        "sideloader-provide": {},
                        "sideloader-start": {},
                        "stdin": {},
                        "swap-middleware": {},
                        "tutkain/add-tap": {},
                        "tutkain/test": {},
                    },
                    "session": sideloader_session_id,
                    "status": ["done"],
                    "versions": {
                        "clojure": {
                            "incremental": 1,
                            "major": 1,
                            "minor": 10,
                            "version-string": "1.10.1",
                        },
                        "java": {
                            "incremental": "2",
                            "major": "11",
                            "minor": "0",
                            "version-string": "11.0.2",
                        },
                        "nrepl": {
                            "incremental": 3,
                            "major": 0,
                            "minor": 8,
                            "version-string": "0.8.3",
                        },
                    },
                }
            )

            # Clone plugin session
            msg = server.recv()
            self.assertEquals({"op", "session", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            plugin_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": plugin_session_id,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            # Clone user session
            msg = server.recv()
            self.assertEquals({"op", "session", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            user_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": user_session_id,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals("Clojure 1.10.1\nnREPL 0.8.3\n", repl.take_print())
        finally:
            server.shutdown()

    def test_handshake(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()

            # Client sends describe op.
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("describe", msg["op"])

            self.capabilities["id"] = msg["id"]
            self.capabilities["session"] = str(uuid.uuid4())
            describe = self.capabilities

            # Server responds, telling the client everything is already sideloaded.
            server.send(describe)

            # Clone plugin session
            msg = server.recv()
            self.assertEquals({"op", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            sideloader_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": sideloader_session_id,
                    "session": str(uuid.uuid4()),
                    "status": ["done"],
                }
            )

            # Client sends sideloader-start.
            self.assertEquals(
                {
                    "id": 1,
                    "op": "sideloader-start",
                    "session": sideloader_session_id,
                },
                server.recv(),
            )

            # Client requires pprint namespace.
            self.assertEquals(
                {
                    "op": "eval",
                    "id": 2,
                    "code": "(require 'tutkain.nrepl.util.pprint)",
                    "session": sideloader_session_id,
                },
                select_keys(server.recv(), {"op", "id", "code", "session"}),
            )

            send_eval_responses(server, sideloader_session_id, 2, "user", "nil")

            # Client asks server to add middleware.
            self.assertEquals(
                {
                    "op": "add-middleware",
                    "middleware": [
                        "tutkain.nrepl.middleware.test/wrap-test",
                        "tutkain.nrepl.middleware.tap/wrap-tap",
                    ],
                    "session": sideloader_session_id,
                    "id": 3,
                },
                server.recv(),
            )

            server.send(
                {
                    "id": 3,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                {
                    "op": "tutkain/add-tap",
                    "session": sideloader_session_id,
                    "id": 4,
                },
                server.recv(),
            )

            server.send(
                {
                    "id": 4,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                {
                    "op": "describe",
                    "session": sideloader_session_id,
                    "id": 5,
                },
                server.recv(),
            )

            describe["id"] = 5
            describe["session"] = sideloader_session_id
            server.send(describe)

            # Clone plugin session
            msg = server.recv()
            self.assertEquals({"op", "session", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            plugin_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": plugin_session_id,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            # Clone user session
            msg = server.recv()
            self.assertEquals({"op", "session", "id"}, msg.keys())
            self.assertEquals("clone", msg["op"])

            user_session_id = str(uuid.uuid4())

            server.send(
                {
                    "id": msg["id"],
                    "new-session": user_session_id,
                    "session": sideloader_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals("Clojure 1.10.1\nnREPL 0.8.3\n", repl.take_print())
        finally:
            server.shutdown()

    def make_sessions(self, server, repl):
        msg = server.recv()
        self.capabilities["id"] = msg["id"]
        server.send(self.capabilities)

        sideloader_session_id = str(uuid.uuid4())

        server.send(
            {
                "id": server.recv()["id"],
                "new-session": sideloader_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        server.recv()

        msg = server.recv()
        server.send(
            {
                "id": msg["id"],
                "session": msg["session"],
                "status": ["done"],
            }
        )

        msg = server.recv()
        server.send(
            {
                "id": msg["id"],
                "session": msg["session"],
                "status": ["done"],
            }
        )

        msg = server.recv()
        server.send(
            {
                "id": msg["id"],
                "session": msg["session"],
                "status": ["done"],
            }
        )

        msg = server.recv()
        self.capabilities["id"] = msg["id"]
        self.capabilities["session"] = msg["session"]
        server.send(self.capabilities)

        plugin_session_id = str(uuid.uuid4())

        server.send(
            {
                "id": server.recv()["id"],
                "new-session": plugin_session_id,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        user_session_id = str(uuid.uuid4())

        server.send(
            {
                "id": server.recv()["id"],
                "new-session": user_session_id,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        repl.take_print()

        return plugin_session_id, user_session_id

    def test_evaluate_form(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            # Client evaluates (inc 1)
            self.set_view_content("(inc 1)")
            self.set_selections((0, 0))
            self.view.run_command("tutkain_evaluate_form")

            # Server receives eval op
            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(inc 1)",
                    "ns": "user",
                    "session": user_session_id,
                    "id": 1,
                },
                select_keys(server.recv(), {"op", "code", "ns", "session", "id"}),
            )

            # Server sends eval responses
            server.send(
                {
                    "id": 1,
                    "ns": "user",
                    "session": user_session_id,
                    "value": "2\n",
                }
            )

            server.send({"id": 1, "ns": "user", "session": user_session_id})

            server.send(
                {
                    "id": 1,
                    "session": user_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals("user=> (inc 1)\n", repl.take_print())
            self.assertEquals("2\n", repl.take_print())
        finally:
            server.shutdown()

    def test_evaluate_view(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            self.set_view_content(
                "(ns app.core) (defn square [x] (* x x)) (comment (square 2))"
            )

            self.view.run_command("tutkain_evaluate_view")

            self.assertEquals(
                {
                    "op": "load-file",
                    "file": "(ns app.core) (defn square [x] (* x x)) (comment (square 2))",
                    "session": plugin_session_id,
                    "id": 1,
                },
                server.recv(),
            )

            server.send(
                {
                    "id": 1,
                    "ns": "user",
                    "session": plugin_session_id,
                    "value": "nil",
                }
            )

            server.send(
                {
                    "id": 1,
                    "session": plugin_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(":tutkain/loaded\n", repl.take_print())
        finally:
            server.shutdown()

    def test_evaluate_form_before_view(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            self.set_view_content(
                cleandoc(
                    """
                (ns my.ns (:require [clojure.set :as set]))

                (defn x [y z] (set/subset? y z))

                (comment
                  (x #{1} #{1 2}))
                """
                )
            )

            self.set_selections((45, 45))
            self.view.run_command("tutkain_evaluate_form")

            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(defn x [y z] (set/subset? y z))",
                    "ns": "my.ns",
                    "session": user_session_id,
                    "id": 1,
                },
                select_keys(server.recv(), {"op", "code", "ns", "session", "id"}),
            )

            # Server can't find namespace.
            server.send(
                {
                    "id": 1,
                    "ns": "my.ns",
                    "session": user_session_id,
                    "status": ["namespace-not-found", "done", "error"],
                }
            )

            # This is an nREPL bug: it sends to "done" responses when it can't find the namespace
            # the user sends.
            server.send(
                {
                    "id": 1,
                    "ns": "my.ns",
                    "session": user_session_id,
                    "status": ["done"],
                }
            )

            # Client evaluates ns form.
            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(ns my.ns (:require [clojure.set :as set]))",
                    "session": user_session_id,
                    "id": 2,
                },
                select_keys(server.recv(), {"op", "code", "session", "id"}),
            )

            server.send({"id": 2, "session": user_session_id, "value": "nil"})
            server.send({"id": 2, "ns": "my.ns", "session": user_session_id})
            server.send({"id": 2, "session": user_session_id, "status": ["done"]})

            # Client retries sending the original form.
            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(defn x [y z] (set/subset? y z))",
                    "ns": "my.ns",
                    "session": user_session_id,
                    "id": 3,
                },
                select_keys(server.recv(), {"op", "code", "ns", "session", "id"}),
            )

            send_eval_responses(server, user_session_id, 3, "my.ns", "#'my.ns/x\n")

            self.assertEquals(
                [
                    "my.ns=> (defn x [y z] (set/subset? y z))\n",
                    "#'my.ns/x\n",
                ],
                repl.take_prints(2),
            )
        finally:
            server.shutdown()

    def test_evaluate_form_switch_views(self):
        server_1 = mock.Server()
        server_2 = mock.Server()

        try:
            repl_1 = TestRepl(self.view.window(), server_1.host, server_1.port).go()
            repl_2 = TestRepl(self.view.window(), server_2.host, server_2.port).go()

            plugin_session_id_1, user_session_id_1 = self.make_sessions(
                server_1, repl_1
            )
            plugin_session_id_2, user_session_id_2 = self.make_sessions(
                server_2, repl_2
            )

            state.set_active_repl_view(repl_1.view)

            self.set_view_content("(inc 1)")
            self.set_selections((0, 0))
            self.view.run_command("tutkain_evaluate_form")

            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(inc 1)",
                    "ns": "user",
                    "session": user_session_id_1,
                    "id": 1,
                },
                select_keys(server_1.recv(), {"op", "code", "ns", "session", "id"}),
            )

            send_eval_responses(server_1, user_session_id_1, 1, "user", "2\n")

            self.assertEquals("user=> (inc 1)\n", repl_1.take_print())
            self.assertEquals("2\n", repl_1.take_print())

            state.set_active_repl_view(repl_2.view)

            self.set_view_content("(inc 2)")
            self.set_selections((0, 0))
            self.view.run_command("tutkain_evaluate_form")

            self.assertEquals(
                {
                    "op": "eval",
                    "code": "(inc 2)",
                    "ns": "user",
                    "session": user_session_id_2,
                    "id": 1,
                },
                select_keys(server_2.recv(), {"op", "code", "ns", "session", "id"}),
            )

            send_eval_responses(server_2, user_session_id_2, 1, "user", "3\n")

            self.assertEquals("user=> (inc 2)\n", repl_2.take_print())
            self.assertEquals("3\n", repl_2.take_print())
        finally:
            server_1.shutdown()
            server_2.shutdown()

    def test_evaluate_view_with_error(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            self.set_view_content("""(ns app.core) (inc "a")""")

            self.view.run_command("tutkain_evaluate_view")

            self.assertEquals(
                {
                    "op": "load-file",
                    "file": """(ns app.core) (inc "a")""",
                    "session": plugin_session_id,
                    "id": 1,
                },
                server.recv(),
            )

            server.send(
                {
                    "err": "Syntax error (ClassCastException) compiling at (REPL:3:1).\nclass java.lang.String cannot be cast to class java.lang.Number (java.lang.String and java.lang.Number are in module java.base of loader 'bootstrap')\n",
                    "id": 1,
                    "session": user_session_id,
                }
            )

            server.send(
                {
                    "ex": "class clojure.lang.Compiler$CompilerException",
                    "id": 1,
                    "root-ex": "class clojure.lang.Compiler$CompilerException",
                    "session": user_session_id,
                    "status": ["eval-error"],
                }
            )

            server.send(
                {
                    "id": 1,
                    "session": user_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                "Syntax error (ClassCastException) compiling at (REPL:3:1).\nclass java.lang.String cannot be cast to class java.lang.Number (java.lang.String and java.lang.Number are in module java.base of loader 'bootstrap')\n",
                repl.take_print(),
            )
        finally:
            server.shutdown()

    def test_run_test_in_current_namespace(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            self.set_view_content(
                cleandoc(
                    """(ns my.test (:require [clojure.test :refer [deftest is]]))

(deftest ok (is (=  2 (+ 1 1))))
(deftest nok (is (=  3 (+ 1 1))))"""
                )
            )

            self.view.run_command("tutkain_run_tests_in_current_namespace")

            self.assertEquals(
                {
                    "op": "eval",
                    "code": """(->> (ns-publics *ns*) (filter (fn [[_ v]] (-> v meta :test))) (run! (fn [[sym _]] (ns-unmap *ns* sym))))""",
                    "session": plugin_session_id,
                    "id": 1,
                },
                select_keys(server.recv(), {"op", "code", "session", "id"}),
            )

            send_eval_responses(server, plugin_session_id, 1, "my.test", "nil")

            self.assertEquals(
                {
                    "file": "(ns my.test (:require [clojure.test :refer [deftest is]]))\n\n(deftest ok (is (=  2 (+ 1 1))))\n(deftest nok (is (=  3 (+ 1 1))))",
                    "id": 2,
                    "op": "load-file",
                    "session": plugin_session_id,
                },
                server.recv(),
            )

            server.send(
                {
                    "id": 2,
                    "ns": "user",
                    "session": plugin_session_id,
                    "value": "nil",
                }
            )

            server.send(
                {
                    "id": 2,
                    "session": plugin_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                {
                    "file": "NO_SOURCE_FILE",
                    "id": 3,
                    "ns": "my.test",
                    "op": "tutkain/test",
                    "session": plugin_session_id,
                },
                server.recv(),
            )

            server.send(
                {
                    "error": [],
                    "fail": [
                        {
                            "actual": "2\n",
                            "expected": "3\n",
                            "file": "NO_SOURCE_FILE",
                            "line": 5,
                            "message": [],
                            "type": "fail",
                            "var-meta": {
                                "column": 1,
                                "file": "NO_SOURCE_FILE",
                                "line": 5,
                                "name": "nok",
                                "ns": "my.test",
                            },
                        }
                    ],
                    "id": 3,
                    "pass": [
                        {
                            "line": 3,
                            "type": "pass",
                            "var-meta": {
                                "column": 1,
                                "file": "NO_SOURCE_FILE",
                                "line": 3,
                                "name": "ok",
                                "ns": "my.test",
                            },
                        }
                    ],
                    "session": plugin_session_id,
                    "summary": "{:test 2, :pass 1, :fail 1, :error 0, :type :summary, :assert 2}",
                }
            )

            server.send(
                {
                    "id": 3,
                    "session": plugin_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                "{:test 2, :pass 1, :fail 1, :error 0, :type :summary, :assert 2}\n",
                repl.take_print(),
            )

            self.assertEquals(
                [sublime.Region(60, 60)], test.regions(self.view, "passes")
            )

            self.assertEquals(
                [sublime.Region(126, 126)], test.regions(self.view, "failures")
            )

            self.assertEquals([], test.regions(self.view, "errors"))
        finally:
            server.shutdown()

    def test_run_test_in_current_namespace_with_error(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            self.set_view_content(
                cleandoc(
                    """(ns my.test (:require [clojure.test :refer [deftest is]]))

(deftest test-with-error (is (= "JavaScript" (+ 1 "a"))))"""
                )
            )

            self.view.run_command("tutkain_run_tests_in_current_namespace")

            self.assertEquals(
                {
                    "op": "eval",
                    "session": plugin_session_id,
                    "id": 1,
                },
                select_keys(server.recv(), {"op", "session", "id"}),
            )

            send_eval_responses(server, plugin_session_id, 1, "my.test", "nil")

            self.assertEquals(
                {
                    "id": 2,
                    "op": "load-file",
                    "session": plugin_session_id,
                },
                select_keys(server.recv(), {"id", "op", "session"}),
            )

            server.send(
                {
                    "id": 2,
                    "ns": "user",
                    "session": plugin_session_id,
                    "value": "nil",
                }
            )

            server.send(
                {
                    "id": 2,
                    "session": plugin_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                {
                    "file": "NO_SOURCE_FILE",
                    "id": 3,
                    "ns": "my.test",
                    "op": "tutkain/test",
                    "session": plugin_session_id,
                },
                server.recv(),
            )

            server.send(
                {
                    "error": [
                        {
                            "actual": "java.lang.ClassCastException: class java.lang.String cannot be cast to class java.lang.Number\n",
                            "expected": '(= "JavaScript" (+ 1 "a"))',
                            "file": "NO_SOURCE_FILE",
                            "line": 153,
                            "message": [],
                            "type": "error",
                            "var-meta": {
                                "column": 1,
                                "file": "NO_SOURCE_FILE",
                                "line": 3,
                                "name": "test-with-error",
                                "ns": "my.test",
                            },
                        }
                    ],
                    "fail": [],
                    "id": 3,
                    "pass": [],
                    "session": plugin_session_id,
                    "summary": "{:test 1, :pass 0, :fail 0, :error 1, :type :summary, :assert 1}",
                }
            )

            server.send(
                {
                    "id": 3,
                    "session": plugin_session_id,
                    "status": ["done"],
                }
            )

            self.assertEquals(
                "{:test 1, :pass 0, :fail 0, :error 1, :type :summary, :assert 1}\n",
                repl.take_print(),
            )

            self.assertEquals([], test.regions(self.view, "passes"))
            self.assertEquals([], test.regions(self.view, "failures"))

            self.assertEquals(
                [sublime.Region(60, 117)], test.regions(self.view, "errors")
            )
        finally:
            server.shutdown()

        def test_run_test_under_cursor(self):
            server = mock.Server()

            try:
                repl = TestRepl(self.view.window(), server.host, server.port).go()
                plugin_session_id, user_session_id = self.make_sessions(server, repl)

                self.set_view_content(
                    cleandoc(
                        """(ns my.test (:require [clojure.test :refer [deftest is]]))

    (deftest ok (is (=  2 (+ 1 1))))
    (deftest nok (is (=  3 (+ 1 1))))"""
                    )
                )

                self.set_selections((93, 93))

                self.view.run_command("tutkain_run_test_under_cursor")

                self.assertEquals(
                    {
                        "op": "eval",
                        "session": plugin_session_id,
                        "id": 1,
                    },
                    select_keys(server.recv(), {"op", "session", "id"}),
                )

                send_eval_responses(server, plugin_session_id, 1, "my.test", "nil")

                self.assertEquals(
                    {
                        "id": 2,
                        "op": "load-file",
                        "session": plugin_session_id,
                    },
                    select_keys(server.recv(), {"id", "op", "session"}),
                )

                server.send(
                    {
                        "id": 2,
                        "ns": "my.test",
                        "session": plugin_session_id,
                        "value": "nil",
                    }
                )

                server.send(
                    {
                        "id": 2,
                        "session": plugin_session_id,
                        "status": ["done"],
                    }
                )

                self.assertEquals(
                    {
                        "file": "NO_SOURCE_FILE",
                        "id": 3,
                        "ns": "my.test",
                        "op": "tutkain/test",
                        "vars": ["nok"],
                        "session": plugin_session_id,
                    },
                    server.recv(),
                )

                server.send(
                    {
                        "error": [],
                        "fail": [
                            {
                                "actual": "2\n",
                                "expected": "3\n",
                                "file": "NO_SOURCE_FILE",
                                "line": 4,
                                "message": [],
                                "type": "fail",
                                "var-meta": {
                                    "column": 1,
                                    "file": "NO_SOURCE_FILE",
                                    "line": 4,
                                    "name": "nok",
                                    "ns": "my.test",
                                },
                            }
                        ],
                        "id": 3,
                        "pass": [],
                        "session": plugin_session_id,
                        "summary": "{:test 1, :pass 0, :fail 1, :error 0, :type :summary, :assert 1}",
                    }
                )

                server.send(
                    {
                        "id": 3,
                        "session": plugin_session_id,
                        "status": ["done"],
                    }
                )

                self.assertEquals(
                    "{:test 1, :pass 0, :fail 1, :error 0, :type :summary, :assert 1}",
                    repl.take_print(),
                )

                self.assertEquals([], test.regions(self.view, "passes"))

                self.assertEquals(
                    [sublime.Region(126, 126)], test.regions(self.view, "failures")
                )

                self.assertEquals([], test.regions(self.view, "errors"))
            finally:
                server.shutdown()

    def test_interrupt(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            self.set_view_content("""(do (Thread/sleep 10000) (println "Boom!"))""")
            self.set_selections((0, 0))
            self.view.run_command("tutkain_evaluate_form")

            server.recv()
            repl.take_print()

            self.view.window().run_command("tutkain_interrupt_evaluation")

            self.assertEquals(
                {"id": 2, "op": "interrupt", "session": user_session_id}, server.recv()
            )

            server.send(
                {
                    "err": "Execution error (InterruptedException) at java.lang.Thread/sleep (Thread.java:-2).\nsleep interrupted\n",
                    "id": 1,
                    "session": user_session_id,
                }
            )

            server.send(
                {
                    "id": 1,
                    "nrepl.middleware.caught/throwable": """{:via [{:type java.lang.InterruptedException,\n        :message "sleep interrupted",\n        :at [java.lang.Thread sleep "Thread.java" -2]}]}""",
                }
            )

            server.send(
                {
                    "ex": "class java.lang.InterruptedException",
                    "id": 1,
                    "root-ex": "class java.lang.InterruptedException",
                    "session": user_session_id,
                    "status": ["eval-error"],
                }
            )

            server.send(
                {
                    "id": 1,
                    "session": user_session_id,
                    "status": ["done", "interrupted"],
                }
            )

            self.assertEquals(
                "Execution error (InterruptedException) at java.lang.Thread/sleep (Thread.java:-2).\nsleep interrupted\n",
                repl.take_print(),
            )

            self.assertEquals(
                """{:via [{:type java.lang.InterruptedException,\n        :message "sleep interrupted",\n        :at [java.lang.Thread sleep "Thread.java" -2]}]}""",
                repl.take_print()
            )
        finally:
            server.shutdown()

    def test_tap(self):
        server = mock.Server()

        try:
            repl = TestRepl(self.view.window(), server.host, server.port).go()
            plugin_session_id, user_session_id = self.make_sessions(server, repl)

            self.set_view_content("(tap> (inc 1))")
            self.set_selections((0, 0))
            self.view.run_command("tutkain_evaluate_form")

            # Discard eval request
            server.recv()

            send_eval_responses(server, user_session_id, 1, "user", "2")
            server.send({"session": user_session_id, "tap": "2\n"})

            self.assertEquals(
                {"session": user_session_id, "tap": "2\n"}, repl.take_tap()
            )
        finally:
            server.shutdown()
