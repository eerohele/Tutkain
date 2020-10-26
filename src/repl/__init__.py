import base64
import os
import sublime
import queue

from threading import Thread
from .session import Session
from . import formatter
from . import views
from .client import Client
from ..log import log
from .. import state


def done(response):
    return response.get("status") == ["done"]


def b64encode_file(path):
    with open(path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")


class Repl(object):
    def __init__(self, window, host, port):
        self.client = Client(host, port).go()
        self.printq = queue.Queue()
        self.tapq = queue.Queue()

        self.view = views.create(window, self.client)
        state.set_view_client(self.view, self.client)
        state.set_active_repl_view(self.view)

    def create_session(self, owner, capabilities, response):
        new_session_id = response["new-session"]
        new_session = Session(new_session_id, self.client)
        new_session.info = capabilities
        self.client.register_session(owner, new_session)
        return new_session

    def create_sessions(self, session, response):
        capabilities = response
        session.info = capabilities
        session.output(response)

        session.send(
            {"op": "clone", "session": session.id},
            handler=lambda response: done(response)
            and self.create_session("plugin", capabilities, response),
        )

        session.send(
            {"op": "clone", "session": session.id},
            handler=lambda response: done(response)
            and self.create_session("user", capabilities, response),
        )

    def handle_sideloader_provide_response(self, session, response):
        if "status" in response and "unexpected-provide" in response["status"]:
            name = response["name"]
            session.output({"err": f"unexpected provide: {name}\n"})

    def sideloader_provide(self, session, response):
        if "name" in response:
            name = response["name"]

            op = {
                "id": response["id"],
                "op": "sideloader-provide",
                "type": response["type"],
                "name": name,
            }

            path = os.path.join(sublime.packages_path(), "tutkain/clojure/src", name)

            if os.path.isfile(path):
                log.debug({"event": "sideloader/provide", "path": path})
                op["content"] = b64encode_file(path)
            else:
                op["content"] = ""

            session.send(
                op,
                handler=lambda response: self.handle_sideloader_provide_response(
                    session, response
                ),
            )

    def describe(self, session):
        session.send(
            {"op": "describe"},
            handler=lambda response: done(response)
            and self.create_sessions(session, response),
        )

    def add_tap(self, session):
        session.send(
            {"op": "tutkain/add-tap"},
            handler=lambda response: done(response) and self.describe(session),
        )

    def add_middleware(self, session):
        session.send(
            {
                "op": "add-middleware",
                "middleware": [
                    "tutkain.nrepl.middleware.test/wrap-test",
                    "tutkain.nrepl.middleware.tap/wrap-tap",
                ],
            },
            handler=lambda response: done(response) and self.add_tap(session),
        )

    def sideload(self, session):
        session.send(
            {"op": "sideloader-start"},
            handler=lambda response: self.sideloader_provide(session, response),
        )

        session.send(
            {"op": "eval", "code": """(require 'tutkain.nrepl.util.pprint)"""},
            pprint=False,
            handler=lambda response: done(response) and self.add_middleware(session),
        )

    def start_formatter(self, settings):
        format_loop = Thread(
            daemon=True,
            target=formatter.format_loop,
            args=(
                self.client.recvq,
                self.printq,
                self.tapq,
                settings,
            ),
        )

        format_loop.name = "tutkain.connection.format_loop"
        format_loop.start()

    def initialize_sessions(self, capabilities, response):
        if "sideloader-start" in capabilities["ops"]:
            session = self.create_session("sideloader", capabilities, response)
            self.start_formatter({"newline_on_done": False})
            self.sideload(session)
        else:
            session = self.create_session("plugin", capabilities, response)
            self.start_formatter({"newline_on_done": True})
            session.output(capabilities)

            self.client.send(
                {"op": "clone"},
                handler=lambda response: done(response)
                and self.create_session("user", capabilities, response),
            )

    def clone(self, response):
        capabilities = response

        self.client.send(
            {"op": "clone"},
            handler=lambda response: done(response)
            and self.initialize_sessions(capabilities, response),
        )

    def go(self):
        self.client.send(
            {"op": "describe"},
            handler=lambda response: done(response) and self.clone(response),
        )

        return self
