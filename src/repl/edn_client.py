from abc import ABC
import itertools
from threading import Lock

from ...api import edn
from ..log import log


class Client(ABC):
    def __init__(self, default_handler):
        self.handlers = {}
        self.message_id = itertools.count(1)
        self.default_handler = default_handler
        self.lock = Lock()

    def register_handler(self, message, handler):
        message = edn.kwmap(message)
        message_id = next(self.message_id)
        message[edn.Keyword("id")] = message_id

        if handler:
            with self.lock:
                self.handlers[message_id] = handler

        return message

    def handle(self, message):
        """Given a message, call the handler function registered for the
        message in this backchannel instance.

        If there's no handler function for the message, call the default
        handler function instead."""
        try:
            if isinstance(message, str):
                self.default_handler(message)
            elif isinstance(message, dict):
                id = message.get(edn.Keyword("id"))

                try:
                    with self.lock:
                        handler = self.handlers.get(id, self.default_handler)

                    handler.__call__(message)
                except AttributeError as error:
                    log.error({"event": "error", "message": message, "error": error})
                finally:
                    with self.lock:
                        self.handlers.pop(id, None)
        except AttributeError:
            raise ValueError(f"Got invalid message: {message}")
