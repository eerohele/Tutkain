import os
from sublime import Window
from ...api import edn
from .. import dialects
from typing import Callable


def read_port(path):
    with open(path, "r") as file:
        return (path, file.read())


def possibilities(folder, dialect):
    if dialect == edn.Keyword("clj"):
        yield os.path.join(folder, ".repl-port")
    elif dialect == edn.Keyword("cljs"):
        yield os.path.join(folder, ".shadow-cljs", "socket-repl.port")


def discover(window, dialect):
    return [
        read_port(port_file)
        for folder in window.folders()
        for port_file in possibilities(folder, dialect)
        if os.path.isfile(port_file)
    ]


def parse(window: Window, port: str, dialect: edn.Keyword, port_gen: Callable):
    if port == "auto":
        if alts := port_gen(window, dialect):
            if alts[0] and (port := alts[0][1]):
                return int(port)
            else:
                window.status_message(
                    f"⚠ File containing port number for a {dialects.name(dialect)} REPL not found."
                )
        else:
            return None
    else:
        return int(port)
