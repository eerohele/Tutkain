from concurrent.futures import TimeoutError
from inspect import cleandoc
from functools import partial
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

from .src import dialects
from .src import selectors
from .src import sexp
from .src import state
from .src import forms
from .src import indent
from .src import inline
from .src import paredit
from .src import namespace
from .src import test
from .src.repl.client import BabashkaClient, JVMClient, JSClient
from .src.repl import info
from .src.repl import history
from .src.repl import tap
from .src.repl import ports
from .src.repl import printer
from .src.repl import views


from .src.log import start_logging, stop_logging


from .api import edn


def make_color_scheme(cache_dir):
    """
    Add the tutkain.repl.stderr scope into the current color scheme.

    We want stderr messages in the same REPL output view as evaluation results, but we don't
    want them to be use syntax highlighting. We can use view.add_regions() to add a scope to such
    messages such that they are not highlighted. Unfortunately, it is not possible to use
    view.add_regions() to only set the foreground color of a region. Furthermore, if we set the
    background color of the scope to use exactly the same color as the global background color of
    the color scheme, Sublime Text refuses to apply the scope.

    We therefore have to resort to this awful hack where every time the plugin is loaded or the
    color scheme changes, we generate a new color scheme in the Sublime Text cache directory. That
    color scheme defines the tutkain.repl.stderr scope which has an almost-transparent background
    color, creating the illusion that we're only setting the foreground color of the text.
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


def evaluate(view, client, code, point=None, handler=None):
    if point:
        line, column = view.rowcol(point)
    else:
        line, column = 0, 0

    file = view.file_name() or "NO_SOURCE_FILE"
    client.recvq.put({edn.Keyword("in"): code})
    client.eval(code, file, line, column, handler)


def source_root():
    return os.path.join(
        sublime.packages_path(), "Tutkain", "clojure", "src", "tutkain"
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

        window.set_layout(layout)


class TutkainClearOutputViewCommand(WindowCommand):
    def clear_view(self, view):
        if view:
            view.set_read_only(False)
            view.run_command("select_all")
            view.run_command("right_delete")
            view.set_read_only(True)
            inline.clear(self.window.active_view())

    def run(self):
        if view := views.active_repl_view(self.window):
            self.clear_view(view)

        panel = self.window.find_output_panel(tap.panel_name)
        panel and self.clear_view(panel)


class TutkainEvaluateFormCommand(TextCommand):
    def run(self, _, scope="outermost", ignore={"comment"}, inline_result=False):
        self.view.window().status_message(
            "tutkain_evaluate_form is deprecated; use tutkain_evaluate instead"
        )

        self.view.run_command("tutkain_evaluate", {
            "scope": scope,
            "ignore": ignore,
            "inline_result": inline_result
        })


class TutkainEvaluateViewCommand(TextCommand):
    def run(self, _):
        self.view.window().status_message(
            "tutkain_evaluate_view is deprecated; use tutkain_evaluate instead"
        )

        self.view.run_command("tutkain_evaluate", {"scope": "view"})


class TutkainRunTests(TextCommand):
    def run(self, _, scope="ns"):
        dialect = edn.Keyword("clj")

        if scope == "ns":
            client = state.client(self.view.window(), dialect)
            dialects.focus_view(self.view, dialect)
            test.run(self.view, client)
        elif scope == "var":
            region = self.view.sel()[0]
            point = region.begin()
            test_var = test.current(self.view, point)

            if test_var:
                client = state.client(self.view.window(), dialect)
                dialects.focus_view(self.view, dialect)
                test.run(self.view, client, test_vars=[test_var])

    def input(self, args):
        if "scope" in args:
            return None
        else:
            return TestScopeInputHandler()


class TestScopeInputHandler(ListInputHandler):
    def placeholder(self):
        return "Choose test scope"

    def list_items(self):
        return [
            sublime.ListInputItem("Var", "var", details="Run the test defined by the var under the caret.", annotation="<code>deftest</code>"),
            sublime.ListInputItem("Namespace", "ns", details="Run all tests in the current namespace."),
        ]


class TutkainRunTestsInCurrentNamespaceCommand(TextCommand):
    def run(self, edit):
        self.view.window().status_message("tutkain_run_tests_in_current_namespace is deprecated; use tutkain_run_tests instead")
        self.view.run_command("tutkain_run_tests", {"scope": "ns"})


class TutkainRunTestUnderCursorCommand(TextCommand):
    def run(self, edit):
        self.view.window().status_message("tutkain_run_test_under_cursor is deprecated; use tutkain_run_tests instead")
        self.view.run_command("tutkain_run_tests", {"scope": "var"})


class DialectInputHandler(ListInputHandler):
    def __init__(self, window):
        self.window = window

    def placeholder(self):
        return "Choose dialect"

    def list_items(self):
        return [
            sublime.ListInputItem("Clojure", "clj", details="A dynamic and functional Lisp that runs on the Java Virtual Machine."),
            sublime.ListInputItem("ClojureScript", "cljs", annotation="shadow-cljs only", details="A compiler for Clojure that targets JavaScript."),
            sublime.ListInputItem("Babashka", "bb", details="A fast, native Clojure scripting runtime.")
        ]

    def confirm(self, value):
        self.dialect = value

    def next_input(self, _):
        return HostInputHandler(self.window, self.dialect)


class HostInputHandler(TextInputHandler):
    def __init__(self, window, dialect):
        self.window = window
        self.dialect = dialect

    def placeholder(self):
        return "Host"

    def validate(self, text):
        return len(text) > 0

    def initial_text(self):
        return "localhost"

    def next_input(self, args):
        return PortInputHandler(self.window, self.dialect)


class PortInputHandler(TextInputHandler):
    def __init__(self, window, dialect):
        self.window = window
        self.dialect = dialect

    def name(self):
        return "port"

    def placeholder(self):
        return "Port"

    def validate(self, text):
        return text.isdigit()

    def initial_text(self):
        alts = ports.discover(self.window, edn.Keyword(self.dialect))

        if alts:
            return alts[0][1]
        else:
            return ""


class TutkainEvaluateInputCommand(WindowCommand):
    def run(self):
        self.window.status_message("tutkain_evaluate_input is deprecated; use tutkain_evaluate instead")
        self.window.active_view().run_command("tutkain_evaluate", {"scope": "input"})


class TutkainEvaluateCommand(TextCommand):
    def without_discard_macro(self, region):
        if region:
            s = sublime.Region(region.begin(), region.begin() + 2)

            if self.view.substr(s) == "#_":
                return sublime.Region(s.end(), region.end())

        return region

    def get_eval_region(self, region, scope="outermost", ignore={}):
        eval_region = region

        if not eval_region.empty():
            return eval_region
        elif scope == "form":
            eval_region = forms.find_adjacent(self.view, region.begin())
        elif scope == "innermost" and (innermost := sexp.innermost(self.view, region.begin(), edge=True)):
            eval_region = innermost.extent()
        elif scope == "outermost" and (outermost := sexp.outermost(self.view, region.begin(), ignore=ignore)):
            eval_region = outermost.extent()

        return self.without_discard_macro(eval_region)

    def evaluate_view(self, client, code):
        client.backchannel.send({
            "op": edn.Keyword("load"),
            "code": code,
            "file": self.view.file_name()
        }, handler=client.recvq.put)

    def handler(self, region, client, response, inline_result):
        if inline_result and edn.Keyword("val") in response:
            inline.clear(self.view)
            inline.show(self.view, region.end(), response[edn.Keyword("val")], inline_result)
        else:
            client.recvq.put(response)

    def evaluate_input(self, client, code):
        evaluate(self.view, client, code)
        history.update(self.view.window(), code)

    def noop(*args):
        pass

    def run(self, edit, scope="outermost", code="", ns=None, ignore={"comment"}, snippet=None, inline_result=False):
        assert scope in {"input", "form", "ns", "innermost", "outermost", "view"}

        point = self.view.sel()[0].begin()
        dialect = dialects.for_point(self.view, point)
        client = state.client(self.view.window(), dialect)

        if client is None:
            self.view.window().status_message(f"ERR: Not connected to a {dialects.name(dialect)} REPL.")
        else:
            dialects.focus_view(self.view, dialect)

            if ns is not None:
                client.switch_namespace(ns)

            if scope == "input":
                view = self.view.window().show_input_panel(
                    "Input: ",
                    history.get(self.view.window()),
                    lambda code: self.evaluate_input(client, code),
                    self.noop,
                    self.noop,
                )

                if snippet:
                    if "$FORMS" in snippet:
                        for index, region in enumerate(self.view.sel()):
                            form = forms.find_adjacent(self.view, region.begin())
                            snippet = snippet.replace(f"$FORMS[{index}]", self.view.substr(form))

                    view.run_command("insert_snippet", {"contents": snippet})

                view.settings().set("tutkain_repl_input_panel", True)
                view.assign_syntax("Clojure (Tutkain).sublime-syntax")
            elif code:
                variables = {}

                for index, region in enumerate(self.view.sel()):
                    if eval_region := self.get_eval_region(region, scope, ignore):
                        variables[str(index)] = self.view.substr(eval_region)

                code = sublime.expand_variables(code, variables)
                evaluate(self.view, client, code)
            elif scope == "view":
                syntax = self.view.syntax()

                if syntax and not syntax.scope in {"source.clojure", "source.clojure.clojure-common"}:
                    self.view.window().status_message(
                        "Active view has incompatible syntax; can't evaluate."
                    )
                else:
                    eval_region = sublime.Region(0, self.view.size())

                    if not eval_region.empty():
                        self.evaluate_view(client, self.view.substr(eval_region))
            elif scope == "ns":
                ns_forms = namespace.forms(self.view)

                for form in ns_forms:
                    code = self.view.substr(form)
                    evaluate(self.view, client, code, point=form.begin())
            else:
                for region in self.view.sel():
                    eval_region = self.get_eval_region(region, scope, ignore)

                    if not eval_region.empty():
                        code = self.view.substr(eval_region)

                        evaluate(
                            self.view,
                            client,
                            code,
                            eval_region.begin(),
                            lambda response: self.handler(eval_region, client, response, inline_result)
                        )

    def input(self, args):
        if any(map(lambda region: not region.empty(), self.view.sel())):
            return None
        if "scope" in args:
            return None
        else:
            return EvaluationScopeInputHandler()


class EvaluationScopeInputHandler(ListInputHandler):
    def name(self):
        return "scope"

    def placeholder(self):
        return "Choose evaluation scope"

    def list_items(self):
        return [
            sublime.ListInputItem("Adjacent Form", "form", details="The form (not necessarily S-expression) adjacent to the caret."),
            sublime.ListInputItem("Innermost S-expression", "innermost", details="The innermost S-expression with respect to the caret position."),
            sublime.ListInputItem("Outermost S-expression", "outermost", details="The outermost S-expression with respect to the caret position.", annotation="ignores (comment)"),
            sublime.ListInputItem("Active View", "view", details="The entire contents of the currently active view."),
            sublime.ListInputItem("Input", "input", details="Tutkain prompts you for input to evaluate."),
            sublime.ListInputItem("Namespace Declarations", "ns", details="Every namespace declaration (<code>ns</code> form) in the active view."),
        ]


class TutkainConnectCommand(WindowCommand):
    def set_build_id(self, view, index, on_done):
        if index == -1:
            view.close()
        else:
            on_done(index)

    def choose_build_id(self, view, ids, on_done):
        items = list(map(lambda id: id.name, ids))

        if items:
            self.window.show_quick_panel(
                items,
                lambda index: self.set_build_id(view, index, on_done),
                placeholder="Choose shadow-cljs build ID",
                flags=sublime.MONOSPACE_FONT
            )

        return True

    def get_project_build_id(self):
        return self.window.project_data().get("settings", {}).get("Tutkain", {}).get("shadow-cljs", {}).get("build-id")

    def get_or_create_view(self, view_id):
        return next(
            filter(lambda view: view.id() == view_id, self.window.views()),
            None,
        ) if view_id else self.window.new_file()

    def run(self, dialect, host, port, view_id=None):
        dialect = edn.Keyword(dialect)

        try:
            active_view = self.window.active_view()
            view = self.get_or_create_view(view_id)

            if settings().get("tap_panel"):
                tap.create_panel(self.window)

            if dialect == edn.Keyword("cljs"):
                def prompt(ids, on_done):
                    self.choose_build_id(view, ids, on_done)

                # FIXME: Backchannel port option
                client = JSClient(source_root(), host, int(port), prompt)
            elif dialect == edn.Keyword("bb"):
                client = BabashkaClient(source_root(), host, int(port))
            else:
                client = JVMClient(
                    source_root(), host, int(port), backchannel_opts={
                        "port": settings().get("clojure").get("backchannel").get("port"),
                        "bind_address": settings().get("clojure").get("backchannel").get("bind_address", "localhost")
                    }
                )

            client.connect()
            set_layout(self.window)
            views.configure(view, dialect, client)
            state.set_view_client(view, dialect, client)
            state.set_repl_view(view, dialect)

            print_loop = Thread(daemon=True, target=printer.print_loop, args=(view, client))
            print_loop.name = f"tutkain.{dialect.name}.print_loop"
            print_loop.start()

            # Activate the output view and the view that was active prior to
            # creating the output view.
            self.window.focus_view(view)
            self.window.focus_view(active_view)
        except TimeoutError:
            view.close()
            sublime.error_message(cleandoc("""
                Timed out trying to connect to socket REPL server.

                Are you trying to connect to an nREPL server? Tutkain no longer supports nREPL.

                See https://tutkain.flowthing.me/#starting-a-socket-repl for more information.
                """))
        except ConnectionRefusedError:
            view.close()
            self.window.status_message(f"ERR: connection to {host}:{port} refused.")

    def input(self, args):
        if "dialect" in args and "host" in args and "port" in args:
            return None
        elif "dialect" in args and "host" in args:
            return PortInputHandler(self.window, args["dialect"])
        elif "dialect" in args:
            return HostInputHandler(self.window, args["dialect"])
        else:
            return DialectInputHandler(self.window)


class TutkainDisconnectCommand(WindowCommand):
    def run(self):
        active_view = self.window.active_view()
        inline.clear(active_view)
        test.progress.stop()

        if view := views.active_repl_view(self.window):
            view.close()

        self.window.focus_view(active_view)


class TutkainNewScratchViewCommand(WindowCommand):
    syntaxes = {
        "Clojure": "Packages/Tutkain/Clojure (Tutkain).sublime-syntax",
        "ClojureScript": "Packages/Tutkain/ClojureScript (Tutkain).sublime-syntax"
    }

    def finish(self, view, index):
        if index == -1:
            view.close()
        else:
            syntax = list(self.syntaxes.values())[index]
            name = list(self.syntaxes.keys())[index]
            view.assign_syntax(syntax)
            view.set_name(f"*scratch* ({name})")
            self.window.focus_view(view)

    def run(self):
        view = self.window.new_file()
        view.set_scratch(True)

        view.window().show_quick_panel(
            self.syntaxes.keys(),
            lambda index: self.finish(view, index),
            placeholder="Choose syntax"
        )


def completion_kinds():
    return {
        "function": sublime.KIND_FUNCTION,
        "var": sublime.KIND_VARIABLE,
        "macro": (sublime.KIND_ID_FUNCTION, "m", "macro"),
        "multimethod": (sublime.KIND_ID_FUNCTION, "u", "multimethod"),
        "namespace": sublime.KIND_NAMESPACE,
        "class": sublime.KIND_TYPE,
        "special-form": (sublime.KIND_ID_FUNCTION, "s", "special form"),
        "method": sublime.KIND_FUNCTION,
        "static-method": sublime.KIND_FUNCTION,
        "keyword": sublime.KIND_KEYWORD,
    }


class TutkainShowPopupCommand(TextCommand):
    def run(self, _, item={}):
        info.show_popup(self.view, -1, {edn.Keyword("info"): edn.kwmap(item)})


class TutkainViewEventListener(ViewEventListener):
    def completion_item(self, item):
        details = ""

        if edn.Keyword("doc") in item:
            d = {}

            for k, v in item.items():
                d[k.name] = v.name if isinstance(v, edn.Keyword) else v

            details = f"""<a href="{sublime.command_url("tutkain_show_popup", args={"item": d})}">More</a>"""

        candidate = item.get(edn.Keyword("candidate"))

        return sublime.CompletionItem(
            trigger=candidate + " ",
            completion=candidate,
            kind=completion_kinds().get(item.get(edn.Keyword("type")).name, sublime.KIND_AMBIGUOUS),
            annotation=" ".join(item.get(edn.Keyword("arglists"), [])),
            details=details,
        )

    def on_query_completions(self, prefix, locations):
        point = locations[0] - 1

        if settings().get("auto_complete") and self.view.match_selector(
            point,
            "source.clojure & (meta.symbol - meta.function.parameters) | (constant.other.keyword - punctuation.definition.keyword)",
        ) and (dialect := dialects.for_point(self.view, point)) and (client := state.client(self.view.window(), dialect)):
            if scope := selectors.expand_by_selector(self.view, point, "meta.symbol | constant.other.keyword"):
                prefix = self.view.substr(scope)

            completion_list = sublime.CompletionList()

            client.backchannel.send({
                "op": edn.Keyword("completions"),
                "prefix": prefix,
                "ns": namespace.name(self.view)
            }, handler=lambda response: (
                completion_list.set_completions(
                    map(self.completion_item, response.get(edn.Keyword("completions"), []))
                )
            ))

            return completion_list


def lookup(view, form, handler):
    if not view.settings().get("tutkain_repl_view_dialect") and form and (
        client := state.client(view.window(), dialects.for_point(view, form.begin()))
    ):
        client.backchannel.send({
            "op": edn.Keyword("lookup"),
            "named": view.substr(form),
            "ns": namespace.name(view)
        }, handler)


class TutkainShowInformationCommand(TextCommand):
    def handler(self, form, response):
        info.show_popup(self.view, form.begin(), response)

    def predicate(self, selector, form):
        return self.view.match_selector(form.begin(), selector)

    def run(self, _, selector="meta.symbol | constant.other.keyword.qualified | constant.other.keyword.auto-qualified", seek_backward=False):
        start_point = self.view.sel()[0].begin()

        if seek_backward:
            form = forms.seek_backward(self.view, start_point, lambda form: self.predicate(selector, form))
        else:
            form = forms.find_adjacent(self.view, start_point)

        lookup(self.view, form, lambda response: self.handler(form, response))


class TutkainGotoDefinitionCommand(TextCommand):
    def handler(self, response):
        info.goto(self.view.window(), info.parse_location(response.get(edn.Keyword("info"))))

    def run(self, _):
        point = self.view.sel()[0].begin()
        form = selectors.expand_by_selector(self.view, point, "meta.symbol")
        lookup(self.view, form, self.handler)


# DEPRECATED
class TutkainShowSymbolInformationCommand(TextCommand):
    def handler(self, form, response):
        info.show_popup(self.view, form.begin(), response)

    def run(self, _):
        self.view.window().status_message("tutkain_show_symbol_information is deprecated; use tutkain_show_information instead")
        point = self.view.sel()[0].begin()
        form = selectors.expand_by_selector(self.view, point, "meta.symbol | constant.other.keyword.qualified | constant.other.keyword.auto-qualified")
        lookup(self.view, form, lambda response: self.handler(form, response))


# DEPRECATED
class TutkainGotoSymbolDefinitionCommand(TextCommand):
    def handler(self, response):
        info.goto(self.view.window(), info.parse_location(response.get(edn.Keyword("info"))))

    def run(self, _):
        self.view.window().status_message("tutkain_goto_symbol_definition is deprecated; use tutkain_goto_definition instead")
        point = self.view.sel()[0].begin()
        form = selectors.expand_by_selector(self.view, point, "meta.symbol")
        lookup(self.view, form, self.handler)


def reconnect(vs):
    for view in filter(views.get_dialect, vs):
        dialect = views.get_dialect(view)
        host = views.get_host(view)
        port = views.get_port(view)

        if dialect and host and port:
            view.window().run_command(
                "tutkain_connect", {
                    "dialect": dialect.name,
                    "host": host,
                    "port": port,
                    "view_id": view.id()
                }
            )


def add_local_regions(view, tuples):
    """Given a set of tuples containing the begin and end point of a Region,
    add a region for each local symbol delimited by the points."""
    if regions := [sublime.Region(begin, end) for begin, end in tuples]:
        view.add_regions(
            "tutkain_locals",
            regions,
            "region.cyanish",
            flags=sublime.DRAW_SOLID_UNDERLINE | sublime.DRAW_NO_FILL | sublime.DRAW_NO_OUTLINE
        )


def symbol_at_point(view, point):
    """Given a view and a point, return the Clojure symbol at the point."""
    if view.match_selector(
        point,
        "meta.symbol - (meta.special-form | variable.function | keyword.declaration.function)"
    ):
        return selectors.expand_by_selector(view, point, "meta.symbol")


class TutkainEventListener(EventListener):
    def on_init(self, views):
        reconnect(views)

    def on_modified_async(self, view):
        inline.clear(view)

    def on_selection_modified_async(self, view):
        if settings().get("highlight_locals", True) and (sel := view.sel()):
            point = sel[0].begin()

            if symbol := symbol_at_point(view, point):
                fetch_locals(view, point, symbol, partial(add_local_regions, view))
            else:
                view.erase_regions("tutkain_locals")

    def on_deactivated_async(self, view):
        inline.clear(view)

    def on_activated(self, view):
        if dialect := view.settings().get("tutkain_repl_view_dialect"):
            state.set_repl_view(view, edn.Keyword(dialect))
        elif settings().get("auto_switch_namespace", True):
            if (dialect := dialects.for_view(view)) and (client := state.client(view.window(), dialect)):
                default_ns = "cljs.user" if dialect == edn.Keyword("cljs") else "user"
                ns = namespace.name(view) or default_ns
                client.switch_namespace(ns)

    def on_hover(self, view, point, hover_zone):
        if settings().get("lookup_on_hover") and view.match_selector(
            point,
            "source.clojure & (meta.symbol | constant.other.keyword.qualified | constant.other.keyword.auto-qualified)"
        ):
            form = forms.find_adjacent(view, point)
            lookup(view, form, lambda response: info.show_popup(view, point, response))

    def on_close(self, view):
        if view.settings().get("tutkain_repl_view_dialect"):
            window = sublime.active_window()
            num_groups = window.num_groups()

            if num_groups == 2 and len(window.views_in_group(num_groups - 1)) == 0:
                window.set_layout({
                    'cells': [[0, 0, 1, 1]],
                    'cols': [0.0, 1.0],
                    'rows': [0.0, 1.0]
                })

    def on_pre_close(self, view):
        if view and (dialect := view.settings().get("tutkain_repl_view_dialect")):
            dialect = edn.Keyword(dialect)

            if client := state.view_client(view, dialect):
                client.halt()

            if window := view.window():
                window.destroy_output_panel(tap.panel_name)
                active_view = window.active_view()

                if active_view:
                    active_view.run_command("tutkain_clear_test_markers")
                    window.focus_view(active_view)

            state.forget_repl_view(view, dialect)


class TutkainExpandSelectionImplCommand(TextCommand):
    """Internal, do not use. Use the tutkain_expand_selection window command
    instead."""
    def run(self, _, point):
        if form := forms.find_adjacent(self.view, point):
            self.view.sel().add(form)
        else:
            self.view.run_command("expand_selection", {"to": "brackets"})


class TutkainExpandSelectionCommand(WindowCommand):
    def run(self):
        view = self.window.active_view()

        for region in view.sel():
            point = region.begin()

            if not region.empty() or selectors.ignore(view, point):
                view.run_command("expand_selection", {"to": "scope"})
            else:
                view.run_command("tutkain_expand_selection_impl", {"point": region.begin()})


class TutkainInterruptEvaluationCommand(WindowCommand):
    def run(self):
        dialect = edn.Keyword("clj")
        client = state.client(self.window, dialect)

        if client is None:
            self.window.status_message("ERR: Not connected to a REPL.")
        else:
            dialects.focus_view(self.window.active_view(), dialect)
            client.backchannel.send({"op": edn.Keyword("interrupt")})


class TutkainInsertNewlineCommand(TextCommand):
    def run(self, edit):
        indent.insert_newline_and_indent(self.view, edit)


class TutkainIndentSexpCommand(TextCommand):
    def get_target_region(self, region, scope):
        if not region.empty():
            return region
        elif scope == "innermost" and (innermost := sexp.innermost(self.view, region.begin())):
            return innermost.extent()
        elif outermost := sexp.outermost(self.view, region.begin()):
            return outermost.extent()

    def run(self, edit, scope="outermost", prune=False):
        assert scope in {"innermost", "outermost"}

        for region in self.view.sel():
            if target := self.get_target_region(region, scope):
                indent.indent_region(self.view, edit, target, prune=prune)


class TutkainPareditForwardCommand(TextCommand):
    def run(self, _, extend=False):
        paredit.move(self.view, True, extend)


class TutkainPareditBackwardCommand(TextCommand):
    def run(self, _, extend=False):
        paredit.move(self.view, False, extend)


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


class TutkainPareditForwardUpCommand(TextCommand):
    def run(self, edit):
        paredit.forward_up(self.view, edit)


class TutkainPareditForwardDownCommand(TextCommand):
    def run(self, edit):
        paredit.forward_down(self.view, edit)


class TutkainPareditBackwardUpCommand(TextCommand):
    def run(self, edit):
        paredit.backward_up(self.view, edit)


class TutkainPareditBackwardDownCommand(TextCommand):
    def run(self, edit):
        paredit.backward_down(self.view, edit)


class TutkainCycleCollectionTypeCommand(TextCommand):
    def run(self, edit):
        sexp.cycle_collection_type(self.view, edit)


class TutkainDiscardUndiscardSexpCommand(TextCommand):
    def run(self, edit, scope="innermost"):
        paredit.discard_undiscard(self.view, edit, scope)


class TutkainReplHistoryListener(EventListener):
    def on_deactivated(self, view):
        if view.settings().get("tutkain_repl_input_panel"):
            history.index = None


class TutkainNavigateReplHistoryCommand(TextCommand):
    def run(self, edit, forward=False):
        history.navigate(self.view, edit, forward=forward)


class TutkainClearTestMarkersCommand(TextCommand):
    def run(self, _):
        self.view.erase_regions(test.region_key(self.view, "passes"))
        self.view.erase_regions(test.region_key(self.view, "failures"))
        self.view.erase_regions(test.region_key(self.view, "errors"))


class TutkainOpenDiffWindowCommand(TextCommand):
    def run(self, _, reference="", actual=""):
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

    def run(self, _):
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


class TutkainChooseEvaluationDialectCommand(WindowCommand):
    dialects = [
        ["clj", "Clojure"],
        ["cljs", "ClojureScript"]
    ]

    def finish(self, index):
        val = self.dialects[index][0]
        self.window.settings().set("tutkain_evaluation_dialect", val)
        self.window.status_message(f"[Tutkain] Evaluating Clojure Common files as {dialects.name(edn.Keyword(val))}")

    def run(self):
        self.window.show_quick_panel(
            self.dialects,
            self.finish,
            placeholder="Choose Clojure Common evaluation dialect"
        )


class TutkainAddRegionsCommand(TextCommand):
    """Implementation detail; do not use."""

    def run(self, _, view_id, regions):
        if self.view.id() == view_id:
            regions = [sublime.Region(begin, end) for begin, end in regions]
            s = self.view.sel()
            s.clear()
            s.add_all(regions)


def handle_locals_response(view, handler, response):
    if positions := response.get(edn.Keyword("positions")):
        handler(positions_to_tuples(view, positions))


def fetch_locals(view, point, form, handler):
    if (
        dialect := dialects.for_point(view, point)
    ) and (
        client := state.client(view.window(), dialect)
    ) and (
        "analyzer.clj" in client.capabilities
    ) and (
        outermost := sexp.outermost(view, point, edge=False)
    ):
        line, column = view.rowcol(form.begin())
        end_column = column + form.size()
        start_line, start_column = view.rowcol(outermost.open.begin())

        client.backchannel.send({
            "op": edn.Keyword("locals"),
            "file": view.file_name() or "NO_SOURCE_FILE",
            "ns": namespace.name(view),
            "context": view.substr(outermost.extent()),
            "form": edn.Symbol(view.substr(form)),
            "start-line": start_line + 1,
            "start-column": start_column + 1,
            "line": line + 1,
            "column": column + 1,
            "end-column": end_column + 1
        }, partial(handle_locals_response, view, handler))


def positions_to_tuples(view, positions):
    regions = []

    if positions:
        for position in positions:
            line = position.get(edn.Keyword("line")) - 1
            column = position.get(edn.Keyword("column")) - 1
            end_column = position.get(edn.Keyword("end-column")) - 1
            begin = view.text_point(line, column)
            end = begin + end_column - column
            regions.append((begin, end))

    return regions


class TutkainSelectUsagesCommand(TextCommand):
    def handler(self, regions):
        # TODO: Why?
        self.view.run_command("tutkain_add_regions", {
            "view_id": self.view.id(),
            "regions": regions
        })

    def run(self, _):
        if sel := self.view.sel():
            point = sel[0].begin()

            if symbol := symbol_at_point(self.view, point):
                fetch_locals(self.view, point, symbol, self.handler)
