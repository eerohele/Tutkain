import os
from ...api import edn


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
