import os

def read_port(path):
    with open(path, "r") as file:
        return (path, file.read())


def possibilities(folder):
    yield os.path.join(folder, ".repl-port")


def discover(window):
    return [
        read_port(port_file)
        for folder in window.folders()
        for port_file in possibilities(folder)
        if os.path.isfile(port_file)
    ]
