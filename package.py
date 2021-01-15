import json
import os
import sublime

from threading import Thread

from sublime_plugin import (
    EventListener,
    ListInputHandler,
    TextCommand,
    TextInputHandler,
    ViewEventListener,
    WindowCommand,
)

from .src import selectors
from .src import sexp
from .src import state
from .src import forms
from .src import indent
from .src import inline
from .src import paredit
from .src import namespace
from .src import test
from .src.repl import Repl
from .src.repl import info
from .src.repl import history
from .src.repl import tap
from .src.repl import printer


from .src.log import log, start_logging, stop_logging


def make_color_scheme(cache_dir):
    """
    Add the tutkain.repl.standard-streams scope into the current color scheme.

    We want stdout/stderr messages in the same REPL output view as evaluation results, but we don't
    want them to be use syntax highlighting. We can use view.add_regions() to add a scope to such
    messages such that they are not highlighted. Unfortunately, it is not possible to use
    view.add_regions() to only set the foreground color of a region. Furthermore, if we set the
    background color of the scope to use exactly the same color as the global background color of
    the color scheme, Sublime Text refuses to apply the scope.

    We therefore have to resort to this awful hack where every time the plugin is loaded or the
    color scheme changes, we generate a new color scheme in the Sublime Text cache directory. That
    color scheme defines the tutkain.repl.stdout scope which has an almost-transparent background
    color, creating the illusion that we're only setting the foreground color of the text.

    Yeah. So, please go give this issue a thumbs-up:

    https://github.com/sublimehq/sublime_text/issues/817
    """
    view = sublime.active_window().active_view()

    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    if view:
        color_scheme = view.settings().get("color_scheme")

        if color_scheme:
            (scheme_name, _) = os.path.splitext(os.path.basename(color_scheme))

            scheme_path = os.path.join(cache_dir, f"{scheme_name}.sublime-color-scheme")

            if not os.path.isfile(scheme_path):
                with open(scheme_path, "w") as scheme_file:
                    scheme_file.write(
                        json.dumps(
                            {
                                "rules": [
                                    {
                                        "name": "Tutkain REPL Standard Output",
                                        "scope": "tutkain.repl.stdout",
                                        "background": "rgba(0, 0, 0, 0.01)",
                                    },
                                    {
                                        "name": "Tutkain REPL Standard Error",
                                        "scope": "tutkain.repl.stderr",
                                        "background": "rgba(0, 0, 0, 0.01)",
                                        "foreground": view.style().get(
                                            "redish", "crimson"
                                        ),
                                    },
                                ]
                            }
                        )
                    )


def settings():
    return sublime.load_settings("Tutkain.sublime-settings")


def plugin_loaded():
    start_logging(settings().get("debug", False))

    preferences = sublime.load_settings("Preferences.sublime-settings")

    cache_dir = os.path.join(sublime.cache_path(), "Tutkain")

    make_color_scheme(cache_dir)
    preferences.add_on_change("Tutkain", lambda: make_color_scheme(cache_dir))


def plugin_unloaded():
    stop_logging()

    for window in sublime.windows():
        window.run_command("tutkain_disconnect")

    view = sublime.active_window().active_view()
    view and inline.clear(view)

    preferences = sublime.load_settings("Preferences.sublime-settings")
    preferences.clear_on_change("Tutkain")


class TutkainClearOutputViewCommand(WindowCommand):
    def clear_view(self, view):
        if view:
            view.set_read_only(False)
            view.run_command("select_all")
            view.run_command("right_delete")
            view.set_read_only(True)
            inline.clear(self.window.active_view())

    def run(self):
        view = state.get_active_repl_view(self.window)

        if view:
            self.clear_view(view)

        panel = self.window.find_output_panel(tap.panel_name)
        panel and self.clear_view(panel)


class TutkainEvaluateFormCommand(TextCommand):
    def handler(self, region, session, file, ns, code, response, inline_result):
        def retry(ns, response):
            if response.get("status") == ["done"]:
                session.send({"op": "eval", "code": code, "file": file, "ns": ns})
            elif "status" in response and "namespace-not-found" in response["status"]:
                session.output(response)

        if "status" in response and "namespace-not-found" in response["status"]:
            ns_region = namespace.find_last(self.view)
            ns_form = sexp.outermost(self.view, ns_region.begin())

            if ns_form:
                session.send(
                    {
                        "op": "eval",
                        "code": self.view.substr(ns_form.extent()),
                        "file": file,
                    },
                    handler=lambda response: retry(ns, response),
                )
        elif inline_result and "value" in response:
            inline.clear(self.view)
            inline.show(self.view, region.end(), response["value"])
        else:
            session.output(response)

    def get_eval_region(self, region, scope="outermost", ignore={}):
        assert scope in {"innermost", "outermost"}

        if not region.empty():
            return region
        else:
            if scope == "outermost":
                outermost = sexp.outermost(self.view, region.begin(), ignore=ignore)
                return outermost and outermost.extent()
            elif scope == "innermost":
                innermost = sexp.innermost(self.view, region.begin(), edge=True)
                return innermost and innermost.extent()

    def run(self, edit, scope="outermost", ignore={"comment"}, inline_result=False):
        session = state.get_session_by_owner(self.view.window(), "user")

        if session is None:
            self.view.window().status_message("ERR: Not connected to a REPL.")
        else:
            for region in self.view.sel():
                eval_region = self.get_eval_region(
                    region, scope=scope, ignore=set(ignore)
                )

                if eval_region:
                    code = self.view.substr(eval_region)
                    ns = namespace.find_declaration(self.view) or "user"
                    file = self.view.file_name()

                    session.output({"in": code, "ns": ns})

                    log.debug(
                        {
                            "event": "send",
                            "scope": "form",
                            "code": code,
                            "file": file,
                            "ns": ns,
                        }
                    )

                    def handler(response):
                        self.handler(
                            eval_region,
                            session,
                            file,
                            ns,
                            code,
                            response,
                            inline_result,
                        )

                    session.send(
                        {"op": "eval", "code": code, "file": file, "ns": ns},
                        handler=handler,
                    )


class TutkainEvaluateViewCommand(TextCommand):
    def handler(self, session, response):
        if "err" in response:
            session.output(response)
            session.denounce(response)
        elif "nrepl.middleware.caught/throwable" in response:
            session.output(response)
        elif response.get("status") == ["done"]:
            if not session.is_denounced(response):
                session.output({"value": ":tutkain/loaded\n"})
                session.output(response)

    def run(self, edit):
        window = self.view.window()
        session = state.get_session_by_owner(window, "plugin")

        if session is None:
            window.status_message("ERR: Not connected to a REPL.")
        else:
            op = {
                "op": "load-file",
                "file": self.view.substr(sublime.Region(0, self.view.size())),
            }

            file_path = self.view.file_name()

            if file_path:
                op["file-name"] = os.path.basename(file_path)
                op["file-path"] = file_path

            session.send(op, handler=lambda response: self.handler(session, response))


class TutkainRunTestsInCurrentNamespaceCommand(TextCommand):
    def run(self, edit):
        session = state.get_session_by_owner(self.view.window(), "plugin")
        test.run(self.view, session)


class TutkainRunTestUnderCursorCommand(TextCommand):
    def run(self, edit):
        region = self.view.sel()[0]
        point = region.begin()
        test_var = test.current(self.view, point)

        if test_var:
            session = state.get_session_by_owner(self.view.window(), "plugin")
            test.run(self.view, session, test_vars=[test_var])


class HostInputHandler(TextInputHandler):
    def __init__(self, window):
        self.window = window

    def placeholder(self):
        return "Host"

    def validate(self, text):
        return len(text) > 0

    def initial_text(self):
        return "localhost"

    def read_port(self, path):
        with open(path, "r") as file:
            return (path, file.read())

    def possibilities(self, folder):
        yield os.path.join(folder, ".nrepl-port")
        yield os.path.join(folder, ".shadow-cljs", "nrepl.port")

        project_port_file = (
            self.window.project_data().get("tutkain", {}).get("nrepl_port_file")
        )

        if project_port_file:
            yield os.path.join(folder, project_port_file)

    def discover_ports(self):
        return [
            self.read_port(port_file)
            for folder in self.window.folders()
            for port_file in self.possibilities(folder)
            if os.path.isfile(port_file)
        ]

    def next_input(self, host):
        ports = self.discover_ports()

        if len(ports) > 1:
            return PortsInputHandler(ports)
        elif len(ports) == 1:
            return PortInputHandler(ports[0][1])
        else:
            return PortInputHandler("")


class PortInputHandler(TextInputHandler):
    def __init__(self, default_value):
        self.default_value = default_value

    def name(self):
        return "port"

    def placeholder(self):
        return "Port"

    def validate(self, text):
        return text.isdigit()

    def initial_text(self):
        return self.default_value


class PortsInputHandler(ListInputHandler):
    def __init__(self, ports):
        self.ports = ports

    def name(self):
        return "port"

    def validate(self, text):
        return text.isdigit()

    def contract_path(self, path):
        return path.replace(os.path.expanduser("~"), "~")

    def list_items(self):
        return list(
            map(lambda x: (f"{x[1]} ({self.contract_path(x[0])})", x[1]), self.ports)
        )


class TutkainEvaluateInputCommand(WindowCommand):
    def eval(self, session, code):
        session.output({"in": code, "ns": session.namespace})
        session.send({"op": "eval", "code": code, "ns": session.namespace})
        history.update(self.window, code)

    def noop(*args):
        pass

    def run(self):
        session = state.get_session_by_owner(self.window, "user")

        if session is None:
            self.window.status_message("ERR: Not connected to a REPL.")
        else:
            view = self.window.show_input_panel(
                "Input: ",
                history.get(self.window),
                lambda code: self.eval(session, code),
                self.noop,
                self.noop,
            )

            view.settings().set("tutkain_repl_input_panel", True)
            view.assign_syntax("Clojure (Tutkain).sublime-syntax")


class TutkainEvaluateCommand(WindowCommand):
    def run(self, code, ns="user"):
        session = state.get_session_by_owner(self.window, "user")

        if session is None:
            self.window.status_message("ERR: Not connected to a REPL.")
        else:
            session.output({"in": code, "ns": ns})
            session.send({"op": "eval", "code": code, "ns": ns})


class TutkainConnectCommand(WindowCommand):
    tap_loop = None

    def set_layout(self):
        # Set up a two-row layout.
        #
        # TODO: Make configurable? This will clobber pre-existing layouts —
        # maybe add a setting for toggling this bit?

        # Only change the layout if the current layout has one row and one column.
        if self.window.get_layout() == {
            'cells': [[0, 0, 1, 1]],
            'cols': [0.0, 1.0],
            'rows': [0.0, 1.0]
        }:
            if settings().get("layout") == "vertical":
                layout = {
                    "cells": [[0, 0, 1, 1], [1, 0, 2, 1]],
                    "cols": [0.0, 0.5, 1.0],
                    "rows": [0.0, 1.0],
                }
            else:
                layout = {
                    "cells": [[0, 0, 1, 1], [0, 1, 1, 2]],
                    "cols": [0.0, 1.0],
                    "rows": [0.0, 0.75, 1.0],
                }

            self.window.set_layout(layout)

    def start_print_loop(self, view, printq):
        print_loop = Thread(
            daemon=True,
            target=printer.print_loop,
            args=(
                view,
                printq,
            ),
        )

        print_loop.name = "tutkain.connection.print_loop"
        print_loop.start()

    def start_tap_loop(self, tapq):
        if settings().get("tap_panel") and self.tap_loop is None:
            self.tap_loop = Thread(
                daemon=True,
                target=tap.tap_loop,
                args=(
                    self.window,
                    tapq,
                ),
            )

            self.tap_loop.name = "tutkain.connection.tap_loop"
            self.tap_loop.start()

    def run(self, host, port):
        try:
            active_view = self.window.active_view()
            self.set_layout()

            repl = Repl(self.window, host, int(port))

            # Activate the output view and the view that was active prior to
            # creating the output view.
            self.window.focus_view(repl.view)
            self.window.focus_view(active_view)

            self.start_print_loop(repl.view, repl.printq)
            self.start_tap_loop(repl.tapq)

            repl.go()
        except ConnectionRefusedError:
            self.window.status_message(f"ERR: connection to {host}:{port} refused.")

    def input(self, args):
        return HostInputHandler(self.window)


class TutkainDisconnectCommand(WindowCommand):
    def run(self):
        inline.clear(self.window.active_view())
        test.progress.stop()
        view = state.get_active_repl_view(self.window)
        view and view.close()


class TutkainNewScratchViewCommand(WindowCommand):
    def run(self):
        view = self.window.new_file()
        view.set_name("*scratch*")
        view.set_scratch(True)
        view.assign_syntax("Clojure (Tutkain).sublime-syntax")
        self.window.focus_view(view)


def completion_kinds():
    if int(sublime.version()) >= 4050:
        return {
            "function": sublime.KIND_FUNCTION,
            "var": sublime.KIND_VARIABLE,
            "macro": (sublime.KIND_ID_FUNCTION, "m", "macro"),
            "namespace": sublime.KIND_NAMESPACE,
            "class": sublime.KIND_TYPE,
            "special-form": (sublime.KIND_ID_FUNCTION, "s", "special form"),
            "method": sublime.KIND_FUNCTION,
            "static-method": sublime.KIND_FUNCTION,
            "keyword": sublime.KIND_KEYWORD,
        }
    else:
        return {}


class TutkainShowPopupCommand(TextCommand):
    def run(self, edit, item={}):
        info.show_popup(self.view, -1, {"info": item})


class TutkainViewEventListener(ViewEventListener):
    def completion_item(self, item):
        return sublime.CompletionItem(
            item.get("candidate"),
            kind=completion_kinds().get(item.get("type"), sublime.KIND_AMBIGUOUS),
            annotation=item.get("arglists", ""),
            details=f"""<a href="{sublime.command_url("tutkain_show_popup", args={"item": item})}">More</a>"""
        )

    def handle_completions(self, completion_list, response):
        completions = map(self.completion_item, response.get("completions", []))
        completion_list.set_completions(completions, flags=sublime.INHIBIT_REORDER)

    def on_query_completions(self, prefix, locations):
        if int(sublime.version()) >= 4050:
            point = locations[0] - 1

            if self.view.match_selector(
                point,
                "(meta.symbol - meta.function.parameters) | (constant.other.keyword - punctuation.definition.keyword)",
            ):
                session = state.get_session_by_owner(self.view.window(), "plugin")

                if session and session.supports("completions"):
                    scope = selectors.expand_by_selector(
                        self.view, point, "meta.symbol | constant.other.keyword"
                    )

                    if scope:
                        prefix = self.view.substr(scope)

                    completion_list = sublime.CompletionList()

                    ns = namespace.find_declaration(self.view)

                    op = {
                        "op": "completions",
                        "prefix": prefix,
                        "options": {"extra-metadata": ["arglists", "doc"]}
                    }

                    if ns:
                        op["ns"] = ns

                    session.send(
                        op,
                        handler=lambda response: self.handle_completions(
                            completion_list, response
                        ),
                    )

                    return completion_list


def lookup(view, point, handler):
    is_repl_output_view = view.settings().get("tutkain_repl_output_view")

    if (
        view.match_selector(point, "source.clojure & meta.symbol")
        and not is_repl_output_view
    ):
        symbol = selectors.expand_by_selector(view, point, "meta.symbol")

        if symbol:
            session = state.get_session_by_owner(view.window(), "plugin")

            # TODO: Cache lookup results?
            if session and session.supports("lookup"):
                op = {"op": "lookup", "sym": view.substr(symbol)}
                ns = namespace.find_declaration(view)

                if ns:
                    op["ns"] = ns

                session.send(op, handler=handler)


class TutkainShowSymbolInformationCommand(TextCommand):
    def run(self, edit):
        lookup(
            self.view,
            self.view.sel()[0].begin(),
            lambda response: info.show_popup(
                self.view, self.view.sel()[0].begin(), response
            ),
        )


class TutkainGotoSymbolDefinitionCommand(TextCommand):
    def run(self, edit):
        lookup(
            self.view,
            self.view.sel()[0].begin(),
            lambda response: info.goto(
                self.view.window(), info.parse_location(response.get("info"))
            ),
        )


class TutkainEventListener(EventListener):
    def on_modified_async(self, view):
        inline.clear(view)

    def on_deactivated_async(self, view):
        inline.clear(view)

    def on_activated(self, view):
        if view.settings().get("tutkain_repl_output_view"):
            state.set_active_repl_view(view)

    def on_hover(self, view, point, hover_zone):
        lookup(view, point, lambda response: info.show_popup(view, point, response))

    def on_pre_close(self, view):
        if view and view.settings().get("tutkain_repl_output_view"):
            window = view.window()
            client = state.get_view_client(view)

            if client:
                client.halt()
                state.forget_repl_view(view)

                # TODO: This sometimes crashes ST.
                #
                # window.set_layout({
                #     'cells': [[0, 0, 1, 1]],
                #     'cols': [0.0, 1.0],
                #     'rows': [0.0, 1.0]
                # })

                window.destroy_output_panel(tap.panel_name)

            if window:
                active_view = window.active_view()

                if active_view:
                    active_view.run_command("tutkain_clear_test_markers")
                    window.focus_view(active_view)


class TutkainExpandSelectionCommand(TextCommand):
    def run(self, edit):
        view = self.view
        selections = view.sel()

        for region in selections:
            if not region.empty() or selectors.ignore(view, region.begin()):
                view.run_command("expand_selection", {"to": "scope"})
            else:
                form = forms.find_adjacent(view, region.begin())
                form and selections.add(form)


class TutkainInterruptEvaluationCommand(WindowCommand):
    def run(self):
        session = state.get_session_by_owner(self.window, "user")

        if session is None:
            self.window.status_message("ERR: Not connected to a REPL.")
        else:
            log.debug({"event": "eval/interrupt", "id": session.id})
            session.send({"op": "interrupt"})


class TutkainInsertNewlineCommand(TextCommand):
    def run(self, edit):
        indent.insert_newline_and_indent(self.view, edit)


class TutkainIndentSexpCommand(TextCommand):
    def run(self, edit, scope="outermost", prune=False):
        for region in self.view.sel():
            if region.empty():
                if scope == "outermost":
                    s = sexp.outermost(self.view, region.begin())
                elif scope == "innermost":
                    s = sexp.innermost(self.view, region.begin())

                if s:
                    indent.indent_region(self.view, edit, s.extent(), prune=prune)
            else:
                indent.indent_region(self.view, edit, region, prune=prune)


class TutkainPareditForwardCommand(TextCommand):
    def run(self, edit):
        paredit.move(self.view, True)


class TutkainPareditBackwardCommand(TextCommand):
    def run(self, edit):
        paredit.move(self.view, False)


class TutkainPareditOpenRoundCommand(TextCommand):
    def run(self, edit):
        paredit.open_bracket(self.view, edit, "(")


class TutkainPareditCloseRoundCommand(TextCommand):
    def run(self, edit):
        paredit.close_bracket(self.view, edit, ")")


class TutkainPareditOpenSquareCommand(TextCommand):
    def run(self, edit):
        paredit.open_bracket(self.view, edit, "[")


class TutkainPareditCloseSquareCommand(TextCommand):
    def run(self, edit):
        paredit.close_bracket(self.view, edit, "]")


class TutkainPareditOpenCurlyCommand(TextCommand):
    def run(self, edit):
        paredit.open_bracket(self.view, edit, "{")


class TutkainPareditCloseCurlyCommand(TextCommand):
    def run(self, edit):
        paredit.close_bracket(self.view, edit, "}")


class TutkainPareditDoubleQuoteCommand(TextCommand):
    def run(self, edit):
        paredit.double_quote(self.view, edit)


class TutkainPareditForwardSlurpCommand(TextCommand):
    def run(self, edit):
        paredit.forward_slurp(self.view, edit)


class TutkainPareditBackwardSlurpCommand(TextCommand):
    def run(self, edit):
        paredit.backward_slurp(self.view, edit)


class TutkainPareditForwardBarfCommand(TextCommand):
    def run(self, edit):
        paredit.forward_barf(self.view, edit)


class TutkainPareditBackwardBarfCommand(TextCommand):
    def run(self, edit):
        paredit.backward_barf(self.view, edit)


class TutkainPareditWrapRoundCommand(TextCommand):
    def run(self, edit):
        paredit.wrap_bracket(self.view, edit, "(")


class TutkainPareditWrapSquareCommand(TextCommand):
    def run(self, edit):
        paredit.wrap_bracket(self.view, edit, "[")


class TutkainPareditWrapCurlyCommand(TextCommand):
    def run(self, edit):
        paredit.wrap_bracket(self.view, edit, "{")


class TutkainPareditForwardDeleteCommand(TextCommand):
    def run(self, edit):
        paredit.forward_delete(self.view, edit)


class TutkainPareditBackwardDeleteCommand(TextCommand):
    def run(self, edit):
        paredit.backward_delete(self.view, edit)


class TutkainPareditRaiseSexpCommand(TextCommand):
    def run(self, edit):
        paredit.raise_sexp(self.view, edit)


class TutkainPareditSpliceSexpCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp(self.view, edit)


class TutkainPareditCommentDwimCommand(TextCommand):
    def run(self, edit):
        paredit.comment_dwim(self.view, edit)


class TutkainPareditSemicolonCommand(TextCommand):
    def run(self, edit):
        paredit.semicolon(self.view, edit)


class TutkainPareditSpliceSexpKillingForwardCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp_killing_forward(self.view, edit)


class TutkainPareditSpliceSexpKillingBackwardCommand(TextCommand):
    def run(self, edit):
        paredit.splice_sexp_killing_backward(self.view, edit)


class TutkainPareditForwardKillFormCommand(TextCommand):
    def run(self, edit):
        paredit.kill_form(self.view, edit, True)


class TutkainPareditBackwardKillFormCommand(TextCommand):
    def run(self, edit):
        paredit.kill_form(self.view, edit, False)


class TutkainPareditBackwardMoveFormCommand(TextCommand):
    def run(self, edit):
        paredit.backward_move_form(self.view, edit)


class TutkainPareditForwardMoveFormCommand(TextCommand):
    def run(self, edit):
        paredit.forward_move_form(self.view, edit)


class TutkainPareditThreadFirstCommand(TextCommand):
    def run(self, edit):
        paredit.thread_first(self.view, edit)


class TutkainPareditThreadLastCommand(TextCommand):
    def run(self, edit):
        paredit.thread_last(self.view, edit)


class TutkainCycleCollectionTypeCommand(TextCommand):
    def run(self, edit):
        sexp.cycle_collection_type(self.view, edit)


class TutkainReplHistoryListener(EventListener):
    def on_deactivated(self, view):
        if view.settings().get("tutkain_repl_input_panel"):
            history.index = None


class TutkainNavigateReplHistoryCommand(TextCommand):
    def run(self, edit, forward=False):
        history.navigate(self.view, edit, forward=forward)


class TutkainClearTestMarkersCommand(TextCommand):
    def run(self, edit):
        self.view.erase_regions(test.region_key(self.view, "passes"))
        self.view.erase_regions(test.region_key(self.view, "failures"))
        self.view.erase_regions(test.region_key(self.view, "errors"))


class TutkainOpenDiffWindowCommand(TextCommand):
    def run(self, edit, reference="", actual=""):
        self.view.window().run_command("new_window")

        window = sublime.active_window()
        window.set_tabs_visible(False)
        window.set_minimap_visible(False)
        window.set_status_bar_visible(False)
        window.set_sidebar_visible(False)
        window.set_menu_visible(False)

        view = window.new_file()
        view.set_name("Tutkain: Diff")
        view.assign_syntax("Clojure (Tutkain).sublime-syntax")
        view.set_scratch(True)
        view.set_reference_document(reference)
        view.run_command("append", {"characters": actual})
        view.set_read_only(True)

        # Hackity hack to try to ensure that the inline diff is open when the diff window opens.
        #
        # I have no idea why this works, or whether it actually even works.
        view.run_command("next_modification")
        view.show(0)

        view.run_command("toggle_inline_diff")


class TutkainShowUnsuccessfulTestsCommand(TextCommand):
    def get_preview(self, region):
        line = self.view.rowcol(region.begin())[0] + 1
        preview = self.view.substr(self.view.line(region)).lstrip()
        return f"{line}: {preview}"

    def run(self, args):
        view = self.view
        failures = test.regions(view, "failures")
        errors = test.regions(view, "errors")
        regions = failures + errors

        if regions:
            regions.sort()

            def goto(i):
                view.set_viewport_position(view.text_to_layout(regions[i].begin()))

            view.window().show_quick_panel(
                [self.get_preview(region) for region in regions],
                goto,
                flags=sublime.MONOSPACE_FONT,
                on_highlight=goto,
            )
