from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from inspect import cleandoc
import io
import queue
import os
import pathlib
import posixpath
import socket
import sublime
import types
import uuid
from threading import Lock, Thread

from . import backchannel
from ...api import edn
from ..log import log
from .. import base64
from .. import dialects
from .. import progress
from .. import settings
from .. import state
from .. import status
from . import formatter
from . import printer
from . import views


def read_until_prompt(socket: socket.SocketType):
    """Given a socket, read bytes from the socket until `=> `, then return the
    read bytes."""
    bs = bytearray()

    while bs[-3:] != bytearray(b"=> "):
        bs.extend(socket.recv(1))

    return bs


BASE64_BLOB = "(def load-base64 (let [decoder (java.util.Base64/getDecoder)] (fn [blob file filename] (with-open [reader (-> decoder (.decode blob) (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader file filename)))))"


class Client(ABC):
    """A `Client` connects to a Clojure socket server, then sends over code
    that a) starts a custom REPL on top of the default REPL and b) starts a
    backchannel socket server. The `Client` then connects to the backchannel
    socket server and uses that connection to communicate with the Clojure
    runtime.

    Tutkain uses the REPL for evaluations and the backchannel for everything
    else (auto-completion, metadata lookup, static analysis, etc.)"""

    def start_workers(self):
        self.executor.submit(self.send_loop)
        self.executor.submit(self.recv_loop)
        return self

    def write_line(self, line):
        """Given a string, write the string followed by a newline into the file object
        associated with the socket of this client."""
        self.buffer.write(line + "\n")
        self.buffer.flush()

    def module_loaded(self, response):
        if response.get(edn.Keyword("result")) == edn.Keyword("ok"):
            self.capabilities.add(response.get(edn.Keyword("filename")))

    def load_modules(self, modules):
        for filename, requires in modules.items():
            path = os.path.join(settings.source_root(), filename)

            with open(path, "rb") as file:
                self.backchannel.send({
                    "op": edn.Keyword("load-base64"),
                    "path": path,
                    "filename": filename,
                    "blob": base64.encode(file.read()),
                    "requires": requires
                }, self.module_loaded)

    @abstractmethod
    def handshake(self):
        pass

    def read_greeting(self):
        greeting = read_until_prompt(self.socket)

        if not self.has_backchannel():
            self.print(greeting.decode("utf-8"))

        return greeting

    def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((self.host, self.port))
        self.buffer = self.socket.makefile(mode="rw")
        log.debug({"event": "client/connect", "host": self.host, "port": self.port})

        log.debug({
            "event": "client/handshake",
            "data": self.executor.submit(self.read_greeting).result(timeout=5)
        })

        return self

    def source_path(self, filename):
        """Given the name of a Clojure source file belonging to this package,
        return the absolute path to that source file as a POSIX path (for
        Windows compatibility)."""
        return posixpath.join(pathlib.Path(settings.source_root()).as_posix(), filename)

    def has_backchannel(self):
        return self.options.get("backchannel", {}).get("enabled", True)

    def __init__(self, host, port, name, dialect, options={}):
        self.id = str(uuid.uuid4())
        self.host = host
        self.port = port
        self.name = name
        self.dialect = dialect
        self.sendq = queue.Queue()
        self.printq = queue.Queue()
        self.executor = ThreadPoolExecutor(thread_name_prefix=f"{self.name}.{self.id}")
        self.backchannel = types.SimpleNamespace(send=lambda *args, **kwargs: None, halt=lambda *args: None)
        self.options = options
        self.capabilities = set()
        self.lock = Lock()
        self.ready = False
        self.on_close = lambda: None

    def send_loop(self):
        """Start a loop that reads strings from `self.sendq` and sends them to
        the Clojure runtime this client is connected to for evaluation."""
        while item := self.sendq.get():
            log.debug({"event": "client/send", "item": item})
            self.write_line(item)

        self.write_line(":repl/quit")
        self.socket.shutdown(socket.SHUT_RDWR)
        log.debug({"event": "thread/exit"})

    @abstractmethod
    def evaluate(self, code, options={"file": "NO_SOURCE_FILE", "line": 0, "column": 0}):
        """Given a string of Clojure code, send it for evaluation to the
        Clojure runtime this client is connected to.

        Accepts a map of options:
        - `file`: the absolute path to the source file this evaluation is
                  associated with (default `"NO_SOURCE_FILE"`)
        - `line`: the line number the code is positioned at (default `0`)
        - `column`: the column number the code is positioned at (default `0`)"""
        pass

    def print(self, item):
        self.printq.put(formatter.format(item))

    def recv_loop(self):
        """Start a loop that reads evaluation responses from a socket and puts
        them in a print queue."""
        try:
            while response := self.socket.recv(io.DEFAULT_BUFFER_SIZE):
                item = response.decode("utf-8")
                log.debug({"event": "client/recv", "item": item})
                self.print(item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            self.print(
                edn.kwmap({
                    "tag": edn.Keyword("err"),
                    "val": f"[Tutkain] Disconnected from {dialects.name(self.dialect)} runtime at {self.host}:{self.port}.\n"
                })
            )

            # Put a None into the queue to tell consumers to stop reading it.
            self.print(None)

            log.debug({"event": "thread/exit"})

            try:
                self.on_close()
                self.buffer.close()
                self.socket.close()
                log.debug({"event": "client/disconnect"})
            except OSError as error:
                log.debug({"event": "error", "exception": error})

    def eval_context_message(self, options):
        message = {
            "op": edn.Keyword("set-eval-context"),
            "file": options.get("file", "NO_SOURCE_FILE") or "NO_SOURCE_FILE",
            "line": options.get("line", 0) + 1,
            "column": options.get("column", 0) + 1
        }

        if ns := options.get("ns"):
            message["ns"] = edn.Symbol(ns)

        if response := options.get("response"):
            message["response"] = edn.kwmap(response)

        return message

    def halt(self):
        """Halt this client."""
        log.debug({"event": "client/halt"})
        self.backchannel.halt()

        # Feed poison pill to input queue.
        self.sendq.put(None)
        self.executor.shutdown(wait=False)


class JVMClient(Client):
    def handshake(self):
        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line("""(clojure.main/repl :prompt (constantly "") :need-prompt (constantly false))""")
        self.write_line("(ns tutkain.bootstrap)")
        self.buffer.readline()
        self.write_line(BASE64_BLOB)
        self.buffer.readline()

        for filename in ["format.clj", "backchannel.clj", "base64.clj", "repl.clj"]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.encode(file.read())
                self.write_line(f"""(load-base64 "{blob}" "{path}" "{os.path.basename(path)}")""")

            self.buffer.readline()

        backchannel_opts = self.options.get("backchannel", {})
        backchannel_port = backchannel_opts.get("port", 0)
        backchannel_bind_address = backchannel_opts.get("bind_address", "localhost")
        self.write_line(f"""(try (tutkain.repl/repl {{:port {backchannel_port} :bind-address "{backchannel_bind_address}"}}) (catch Exception ex (.toString ex)))""")
        line = self.buffer.readline()

        if not line.startswith('{'):
            self.print(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "Couldn't connect to Clojure REPL.\n"
            }))

            self.print(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": line + "\n"
            }))

            self.print(edn.kwmap({
                "tag": edn.Keyword("err"),
                "val": "NOTE: Tutkain requires Clojure 1.10.0 or newer.\n"
            }))
        else:
            ret = edn.read(line)

            if (host := ret.get(edn.Keyword("host"))) and (port := ret.get(edn.Keyword("port"))):
                self.backchannel = backchannel.Client(self.print).connect(self.id, host, port)
                self.print(edn.kwmap({"tag": edn.Keyword("out"), "val": ret.get(edn.Keyword("greeting"))}))
            else:
                self.print(ret)

        self.load_modules({
            "java.clj": [],
            "lookup.clj": [],
            "completions.clj": [],
            "load_blob.clj": [],
            "test.clj": [],
            "query.clj": [],
            "clojuredocs.clj": [],
            "analyzer.clj": [
                edn.Symbol("clojure.tools.reader"),
                edn.Symbol("clojure.tools.analyzer.ast")
            ],
            "analyzer/jvm.clj": [
                edn.Symbol("tutkain.analyzer"),
                edn.Symbol("clojure.tools.analyzer.jvm")
            ]
        })

    def __init__(self, host, port, options={}):
        super().__init__(host, port, "tutkain.clojure.client", edn.Keyword("clj"), options=options)

    def connect(self):
        super().connect()

        if self.has_backchannel():
            self.handshake()

        self.start_workers()
        return self

    def evaluate(self, code, options={"file": "NO_SOURCE_FILE", "line": 0, "column": 0}):
        self.print(edn.kwmap({"tag": edn.Keyword("in"), "val": code + "\n"}))

        if self.has_backchannel():
            self.backchannel.send(
                self.eval_context_message(options),
                lambda _: self.sendq.put(code)
            )
        else:
            self.sendq.put(code)


class JSClient(Client):
    def __init__(self, host, port, options={}):
        super().__init__(host, port, "tutkain.cljs.client", edn.Keyword("cljs"), options=options)

    def connect(self):
        super().connect()
        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line('(clojure.main/repl :prompt (constantly "") :need-prompt (constantly false))')
        self.write_line("""(sort (shadow.cljs.devtools.api/get-build-ids))""")
        build_id_options = edn.read_line(self.buffer)

        if build_id := self.options.get("build_id"):
            self.handshake(build_id)
        else:
            self.executor.submit(
                self.options.get("prompt_for_build_id"),
                build_id_options,
                lambda index: self.handshake(build_id_options[index])
            )

        return self

    def handshake(self, build_id):
        self.write_line("(ns tutkain.bootstrap)")
        self.buffer.readline()
        self.write_line(BASE64_BLOB)
        self.buffer.readline()

        for filename in ["format.clj", "backchannel.clj", "base64.clj", "shadow.clj"]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.encode(file.read())
                self.write_line(f"""(load-base64 "{blob}" "{path}" "{os.path.basename(path)}")""")

            self.buffer.readline()

        backchannel_port = self.options.get("backchannel", {}).get("port", 0)
        self.write_line(f"""(tutkain.shadow/repl {{:build-id {build_id} :port {backchannel_port}}})""")

        ret = edn.read_line(self.buffer)
        host = ret.get(edn.Keyword("host"))
        port = ret.get(edn.Keyword("port"))
        self.backchannel = backchannel.Client(self.print).connect(self.id, host, port)
        greeting = ret.get(edn.Keyword("greeting"))
        self.print(edn.kwmap({"tag": edn.Keyword("out"), "val": greeting}))

        # NOTE: If you make changes to module loading, make sure you manually
        # test connecting to a ClojureScript runtime *without* connecting to
        # a Clojure runtime first to make sure we're loading everything we
        # need.
        self.load_modules({
            "lookup.clj": [],
            "java.clj": [],
            "completions.clj": [],
            "query.clj": [],
            "cljs.clj": [],
            "shadow.clj": [],
            "analyzer.clj": [
                edn.Symbol("clojure.tools.reader"),
                edn.Symbol("clojure.tools.analyzer.ast")
            ],
            "analyzer/js.clj": [
                edn.Symbol("tutkain.analyzer")
            ]
        })

        self.start_workers()

    def evaluate(self, code, options={"file": "NO_SOURCE_FILE", "line": 0, "column": 0}):
        self.print(edn.kwmap({"tag": edn.Keyword("in"), "val": code + "\n"}))

        if self.has_backchannel():
            self.backchannel.send(
                self.eval_context_message(options),
                lambda _: self.sendq.put(code)
            )
        else:
            self.sendq.put(code)


class BabashkaClient(Client):
    def __init__(self, host, port):
        super().__init__(host, port, "tutkain.bb.client", edn.Keyword("bb"))

    def handshake(self):
        pass

    def connect(self):
        super().connect()
        self.start_workers()
        return self

    def has_backchannel(self):
        return False

    def evaluate(self, code, options={"file": "NO_SOURCE_FILE", "line": 0, "column": 0}):
        self.print(edn.kwmap({"tag": edn.Keyword("in"), "val": code + "\n"}))
        self.sendq.put(code)


def set_layout(window):
    # Set up a two-row layout.
    #
    # TODO: Make configurable? This will clobber pre-existing layouts —
    # maybe add a setting for toggling this bit?

    # Only change the layout if the current layout has one row and one column.
    if window.get_layout() == {
        "cells": [[0, 0, 1, 1]],
        "cols": [0.0, 1.0],
        "rows": [0.0, 1.0],
    }:
        if settings.load().get("layout") == "vertical":
            layout = {
                "cells": [[0, 0, 1, 1], [1, 0, 2, 1]],
                "cols": [0.0, 0.5, 1.0],
                "rows": [0.0, 1.0],
            }
        else:
            layout = {
                "cells": [[0, 0, 1, 1], [0, 1, 1, 2]],
                "cols": [0.0, 1.0],
                "rows": [0.0, 0.5, 1.0],
            }

        window.set_layout(layout)


def start(view, client):
    window = view.window() or sublime.active_window()
    active_view = window.active_view()
    views.create_tap_panel(view)

    try:
        client.connect()
        state.register_connection(view, window, client)

        if view.element() is None:
            set_layout(window)

        views.configure(view, client.dialect, client.id, client.host, client.port, settings.load().get("repl_view_settings", {}))

        if client.dialect == edn.Keyword("bb") or (not client.has_backchannel() and len(state.get_connections()) == 1):
            view.assign_syntax("Plain Text.tmLanguage")

        client.ready = True

        if view.element() is None:
            window.focus_view(view)
        else:
            views.show_output_panel(window)
            state.on_activated(window, active_view)

        status.set_connection_status(active_view, client)

        return client
    except TimeoutError:
        view.close()
        sublime.error_message(cleandoc("""
            Timed out trying to connect to socket REPL server.

            Are you trying to connect to an nREPL server? Tutkain no longer supports nREPL.

            See https://tutkain.flowthing.me/#starting-a-socket-repl for more information.
            """))


def start_printer(client, view, options={}):
    print_loop = Thread(daemon=True, target=printer.print_loop, args=(view, client, options))
    print_loop.name = f"tutkain.{client.id}.print_loop"
    print_loop.start()
    return print_loop


def on_select_disconnect_connection(connection):
    if connection:
        window = sublime.active_window()
        active_view = window.active_view()

        try:
            connection.client.halt()
            connection.view.close()
        finally:
            window.focus_view(active_view)


def make_quick_panel_item(connection):
    if connection.view.element() is None:
        output = "view"
    else:
        output = "panel"

    annotation = f"{dialects.name(connection.client.dialect)} ({output})"
    trigger = f"{connection.client.host}:{connection.client.port}"
    return sublime.QuickPanelItem(trigger, annotation=annotation)


def stop(window):
    if connections := list(filter(lambda this: this.window.id() == window.id(), state.get_connections().values())):
        progress.stop()

        if len(connections) == 1:
            on_select_disconnect_connection(connections[0])
        else:
            window.show_quick_panel(
                list(map(make_quick_panel_item, connections)),
                lambda index: index != -1 and on_select_disconnect_connection(connections[index]),
                placeholder="Choose the connection to close"
            )
    # Close phantom views resulting from the REPL server dying
    elif vs := filter(lambda view: views.get_client_id(view), window.views()):
        for view in vs:
            view.close()
