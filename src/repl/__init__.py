import datetime
import io
import os
import pathlib
import posixpath
import queue
import socket
import types
import uuid
from abc import abstractmethod
from concurrent.futures import ThreadPoolExecutor
from inspect import cleandoc
from threading import Thread

import sublime

from ...api import edn
from .. import base64, dialects, progress, settings, state, status
from ..log import log
from . import backchannel, formatter, printer, views, edn_client


def read_until_prompt(socket: socket.SocketType):
    """Given a socket, read bytes from the socket until `=> `, then return the
    read bytes."""
    bs = bytearray()

    while bs[-3:] != bytearray(b"=> "):
        bs.extend(socket.recv(1))

    return bs


BASE64_BLOB = """(intern (create-ns 'tutkain.repl) 'load-base64 #?(:bb (fn [blob _ _] (load-string (String. (.decode (java.util.Base64/getDecoder) blob) "UTF-8"))) :clj (fn [blob file filename] (with-open [reader (-> (java.util.Base64/getDecoder) (.decode blob) (java.io.ByteArrayInputStream.) (java.io.InputStreamReader.) (clojure.lang.LineNumberingPushbackReader.))] (clojure.lang.Compiler/load reader file filename)))))"""


class Client(edn_client.Client):
    """A `Client` connects to a Clojure socket server, then sends over code
    that a) starts a custom REPL on top of the default REPL and b) starts a
    backchannel socket server. The `Client` then connects to the backchannel
    socket server and uses that connection to communicate with the Clojure
    runtime.

    Tutkain uses the REPL for evaluations and the backchannel for everything
    else (auto-completion, metadata lookup, static analysis, etc.)"""

    connection_err_msg = "NOTE: Tutkain requires Clojure 1.10.0 or newer.\n"

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
        if response.get(edn.Keyword("tag")) == edn.Keyword("ret"):
            self.capabilities.add(response.get(edn.Keyword("val")))

    def load_modules(self):
        for filename, requires in self.modules.items():
            path = os.path.join(settings.source_root(), filename)

            with open(path, "rb") as file:
                self.send_op(
                    {
                        "op": edn.Keyword("load-base64"),
                        "path": path,
                        "filename": filename,
                        "blob": base64.encode(file.read()),
                        "requires": requires,
                    },
                    self.module_loaded,
                )

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

        log.debug(
            {
                "event": "client/handshake",
                "data": self.executor.submit(self.read_greeting).result(timeout=5),
            }
        )

        return self

    def source_path(self, filename):
        """Given the name of a Clojure source file belonging to this package,
        return the absolute path to that source file as a POSIX path (for
        Windows compatibility)."""
        return posixpath.join(pathlib.Path(settings.source_root()).as_posix(), filename)

    def has_backchannel(self):
        return self.options.get("backchannel", {}).get("enabled", True)

    def __init__(self, host, port, mode, name, dialect, options={}):
        assert mode in {"repl", "rpc"}

        super().__init__(self.print)

        self.since = datetime.datetime.now()
        self.id = str(uuid.uuid4())
        self.host = host
        self.port = port
        self.name = name
        self.dialect = dialect
        self.sendq = queue.Queue()
        self.printq = queue.Queue()
        self.executor = ThreadPoolExecutor(thread_name_prefix=f"{self.name}.{self.id}")
        self.backchannel = types.SimpleNamespace(
            send=lambda *args, **kwargs: None, halt=lambda *args: None
        )
        self.mode = mode
        self.options = options
        self.capabilities = set()
        self.ready = False
        self.on_close = lambda: None

    def send(self, message):
        if isinstance(message, dict):
            edn.write_line(self.buffer, message)
        else:
            self.write_line(message)

    def send_loop(self):
        """Start a loop that reads strings from `self.sendq` and sends them to
        the Clojure runtime this client is connected to for evaluation."""
        while item := self.sendq.get():
            log.debug({"event": "client/send", "item": item})
            self.send(item)

        self.write_line("{:op :quit}")
        self.socket.shutdown(socket.SHUT_RDWR)
        log.debug({"event": "thread/exit"})

    def evaluate_repl(
        self, code, options={"file": "NO_SOURCE_FILE", "line": 0, "column": 0}
    ):
        """Given a string of Clojure code, send it for evaluation to the
        Clojure runtime this client is connected to.

        Accepts a map of options:
        - `file`: the absolute path to the source file this evaluation is
                  associated with (default `"NO_SOURCE_FILE"`)
        - `line`: the line number the code is positioned at (default `0`)
        - `column`: the column number the code is positioned at (default `0`)"""
        if self.has_backchannel():
            self.backchannel.send(
                {"op": edn.Keyword("set-thread-bindings"), **options},
                lambda _: self.sendq.put(code),
            )
        else:
            self.sendq.put(code)

    def evaluate_rpc(
        self,
        code,
        handler,
        options={"file": "NO_SOURCE_FILE", "line": 0, "column": 0},
    ):
        """Given a string of Clojure code, send it for evaluation to the
        Clojure runtime this client is connected to.

        Accepts an evaluation result handler function and and a map of options:
        - `file`: the absolute path to the source file this evaluation is
                  associated with (default `"NO_SOURCE_FILE"`)
        - `line`: the line number the code is positioned at (default `0`)
        - `column`: the column number the code is positioned at (default `0`)"""
        message = {
            "op": edn.Keyword("eval"),
            "dialect": self.dialect,
            "code": code,
            **options,
        }

        if self.mode == "repl" and self.has_backchannel():
            self.backchannel.send(message, handler)
        else:
            message = self.register_handler(message, handler)
            self.sendq.put(message)

    def print(self, item):
        self.printq.put(formatter.format(item))

    def recv(self):
        if self.mode == "rpc":
            return edn.read_line(self.buffer)
        else:
            return self.socket.recv(io.DEFAULT_BUFFER_SIZE).decode("utf-8")

    def send_op(self, message, handler=None):
        if self.mode == "repl" and self.has_backchannel():
            self.backchannel.send(message, handler)
        else:
            message = self.register_handler(message, handler)
            self.sendq.put(message)

    def recv_loop(self):
        """Start a loop that reads evaluation responses from a socket and calls the handler function on them."""
        try:
            while item := self.recv():
                log.debug({"event": "client/recv", "item": item})
                self.handle(item)
        except OSError as error:
            log.error({"event": "error", "error": error})
        finally:
            self.print(
                edn.kwmap(
                    {
                        "tag": edn.Keyword("err"),
                        "val": f"[Tutkain] Disconnected from {dialects.name(self.dialect)} runtime at {self.host}:{self.port}.\n",
                    }
                )
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

    def halt(self):
        """Halt this client."""
        log.debug({"event": "client/halt"})
        self.backchannel.halt()

        # Feed poison pill to input queue.
        self.sendq.put(None)
        self.executor.shutdown(wait=False)


class JVMClient(Client):
    modules = {
        "java.cljc": [],
        "lookup.cljc": [],
        "completions.cljc": [],
        "load_blob.cljc": [],
        "test.cljc": [],
        "query.cljc": [],
        "deps.clj": [
            edn.Symbol("clojure.repl.deps"),
        ],
        "clojuredocs.clj": [],
        "analyzer.clj": [
            edn.Symbol("clojure.tools.reader"),
            edn.Symbol("clojure.tools.analyzer.ast"),
        ],
        "analyzer/jvm.clj": [
            edn.Symbol("tutkain.analyzer"),
            edn.Symbol("clojure.tools.analyzer.jvm"),
        ],
    }

    def handshake(self):
        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line(
            """(clojure.main/repl :init (constantly nil) :prompt (constantly "") :need-prompt (constantly false))"""
        )
        self.write_line(BASE64_BLOB)
        self.buffer.readline()

        for filename in [
            "pprint.cljc",
            "format.cljc",
            "base64.cljc",
            "rpc.cljc",
            "repl.cljc",
        ]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.encode(file.read())
                self.write_line(
                    f"""(tutkain.repl/load-base64 "{blob}" "{path}" "{os.path.basename(path)}")"""
                )

            self.buffer.readline()

        init = self.options.get("init") or "tutkain.rpc/default-init"
        add_tap = self.options.get("add_tap", False)

        if self.mode == "repl":
            backchannel_opts = self.options.get("backchannel", {})
            backchannel_port = backchannel_opts.get("port", 0)
            backchannel_bind_address = backchannel_opts.get("bind_address", "localhost")
            self.write_line(
                f"""(tutkain.repl/repl {{:init `{init} :add-tap? {"true" if add_tap else "false"} :port {backchannel_port} :bind-address "{backchannel_bind_address}"}})"""
            )
            line = self.buffer.readline()

            ret = edn.read(line)

            if ret.get(edn.Keyword("tag")) == edn.Keyword("err"):
                self.print(ret)
            elif (host := ret.get(edn.Keyword("host"))) and (
                port := ret.get(edn.Keyword("port"))
            ):
                self.backchannel = backchannel.Client(self.print).connect(
                    self.id, host, port
                )
            else:
                self.print(ret)
        else:
            self.write_line(
                f"""(tutkain.rpc/rpc {{:init `{init} :add-tap? {"true" if add_tap else "false"}}})"""
            )

            line = self.buffer.readline()
            ret = edn.read(line)
            self.print(ret)

        self.load_modules()

    def __init__(self, host, port, mode, options={}):
        super().__init__(
            host,
            port,
            mode,
            "tutkain.clojure.client",
            edn.Keyword("clj"),
            options=options,
        )

    def connect(self):
        super().connect()

        if self.has_backchannel() or self.mode == "rpc":
            self.handshake()

        self.start_workers()
        return self


class JSClient(Client):
    # NOTE: If you make changes to module loading, make sure you manually
    # test connecting to a ClojureScript runtime *without* connecting to
    # a Clojure runtime first to make sure we're loading everything we
    # need.
    modules = {
        "lookup.cljc": [],
        "java.cljc": [],
        "completions.cljc": [],
        "query.cljc": [],
        "cljs.clj": [],
        "shadow.clj": [],
        "analyzer.clj": [
            edn.Symbol("clojure.tools.reader"),
            edn.Symbol("clojure.tools.analyzer.ast"),
        ],
        "analyzer/js.clj": [edn.Symbol("tutkain.analyzer")],
    }

    def __init__(self, host, port, options={}):
        super().__init__(
            host,
            port,
            "rpc",
            "tutkain.cljs.client",
            edn.Keyword("cljs"),
            options=options,
        )

    def connect(self):
        super().connect()
        # Start a promptless REPL so that we don't need to keep sinking the prompt.
        self.write_line(
            '(clojure.main/repl :init (constantly nil) :prompt (constantly "") :need-prompt (constantly false))'
        )
        self.write_line("""(sort (shadow.cljs.devtools.api/get-build-ids))""")
        build_id_options = edn.read_line(self.buffer)

        if build_id := self.options.get("build_id"):
            self.handshake(build_id)
        else:
            self.executor.submit(
                self.options.get("prompt_for_build_id"),
                build_id_options,
                lambda index: self.handshake(build_id_options[index]),
            )

        return self

    def evaluate(
        self, code, options={"file": "NO_SOURCE_FILE", "line": 0, "column": 0}
    ):
        self.evaluate_rpc(code, options)

    def handshake(self, build_id):
        self.write_line(BASE64_BLOB)
        self.buffer.readline()

        for filename in [
            "pprint.cljc",
            "format.cljc",
            "base64.cljc",
            "rpc.cljc",
            "shadow.clj",
        ]:
            path = self.source_path(filename)

            with open(path, "rb") as file:
                blob = base64.encode(file.read())
                self.write_line(
                    f"""(tutkain.repl/load-base64 "{blob}" "{path}" "{os.path.basename(path)}")"""
                )

            self.buffer.readline()

        self.write_line(f"""(tutkain.shadow/rpc {{:build-id {build_id}}})""")

        self.load_modules()
        self.start_workers()


class BabashkaClient(JVMClient):
    connection_err_msg = "NOTE: Tutkain requires Babashka v1.1.171 or newer.\n"

    modules = {
        "java.cljc": [],
        "lookup.cljc": [],
        "completions.cljc": [],
        "load_blob.cljc": [],
        "test.cljc": [],
        "query.cljc": [],
    }

    def __init__(self, host, port, mode, options={}):
        super(JVMClient, self).__init__(
            host, port, mode, "tutkain.bb.client", edn.Keyword("bb"), options=options
        )


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

        views.configure(
            view,
            client.dialect,
            client.id,
            client.host,
            client.port,
            settings.load().get("repl_view_settings", {}),
        )

        if not client.has_backchannel() and len(state.get_connections()) == 1:
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
        sublime.error_message(
            cleandoc(
                """
            Timed out trying to connect to socket REPL server.

            Are you trying to connect to an nREPL server? Tutkain no longer supports nREPL.

            See https://tutkain.flowthing.me/#starting-a-socket-repl for more information.
            """
            )
        )


def start_printer(client, view, options={}):
    print_loop = Thread(
        daemon=True, target=printer.print_loop, args=(view, client, options)
    )
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

    now = datetime.datetime.now()
    delta = now - connection.client.since
    delta = delta - datetime.timedelta(microseconds=delta.microseconds)
    annotation = f"{dialects.name(connection.client.dialect)} · {output.capitalize()} · Uptime {delta}"
    trigger = f"{connection.client.host}:{connection.client.port}"
    return sublime.QuickPanelItem(trigger, annotation=annotation)


def stop(window):
    if connections := list(
        filter(
            lambda this: this.window.id() == window.id(),
            state.get_connections().values(),
        )
    ):
        progress.stop()

        if len(connections) == 1:
            on_select_disconnect_connection(connections[0])
        else:
            window.show_quick_panel(
                list(map(make_quick_panel_item, connections)),
                lambda index: index != -1
                and on_select_disconnect_connection(connections[index]),
                placeholder="Choose the connection to close",
            )
    # Close phantom views resulting from the REPL server dying
    elif vs := filter(lambda view: views.get_client_id(view), window.views()):
        for view in vs:
            view.close()

    if view := window.active_view():
        status.erase_connection_status(view)


def backchannel_options(project_data, dialect, backchannel=True):
    dialect_name_lower = dialects.name(dialect).lower()

    return {
        **(settings.backchannel_options(dialect, backchannel) or {}),
        **(project_data or {})
        .get("tutkain", {})
        .get(dialect_name_lower, {})
        .get("backchannel", {}),
    }
