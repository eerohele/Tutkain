from functools import partial
import json
import os
import sublime

from sublime_plugin import (
    EventListener,
    ListInputHandler,
    TextCommand,
    TextInputHandler,
    ViewEventListener,
    WindowCommand,
)

from .src import base64
from .src import dialects
from .src import selectors
from .src import sexp
from .src import state
from .src import status
from .src import forms
from .src import indent
from .src import inline
from .src import paredit
from .src import progress
from .src import namespace
from .src import test
from .src import repl
from .src import completions
from .src import settings
from .src.repl import info
from .src.repl import query
from .src.repl import history
from .src.repl import ports


from .src.log import start_logging, stop_logging


from .api import edn


def make_color_scheme(cache_dir):
    """
    Add the tutkain.repl.stderr scope into the current color scheme.

    We want stderr messages in the same REPL output view as evaluation results, but we don't
    want them to use syntax highlighting. We can use view.add_regions() to add a scope to such
    messages such that they are not highlighted. Unfortunately, it is not possible to use
    view.add_regions() to only set the foreground color of a region. Furthermore, if we set the
    background color of the scope to use exactly the same color as the global background color of
    the color scheme, Sublime Text refuses to apply the scope.

    We therefore have to resort to this awful hack where every time the plugin is loaded or the
    color scheme changes, we generate a new color scheme in the Sublime Text cache directory. That
    color scheme defines the tutkain.repl.stderr scope which has an almost-transparent background
    color, creating the illusion that we're only setting the foreground color of the text.
    """
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)

    if view := sublime.active_window().active_view():
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


def plugin_loaded():
    start_logging(settings.load().get("debug", False))
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


def evaluate(view, client, code, point=None, options={}):
    if point:
        line, column = view.rowcol(point)
    else:
        line, column = 0, 0

    options["line"] = line
    options["column"] = column
    client.evaluate(code, options)

class TemporaryFileEventListener(ViewEventListener):
    @classmethod
    def is_applicable(_, settings):
        return settings.has("tutkain_temp_file")

    def on_load(self):
        try:
            if temp_file := self.view.settings().get("tutkain_temp_file"):
                path = temp_file.get("path")
                descriptor = temp_file.get("descriptor")

                if name := temp_file.get("name"):
                    self.view.set_name(name)

                if path and descriptor and os.path.exists(path):
                    os.close(descriptor)
                    os.remove(path)
        except:
            pass


class TutkainClearOutputViewCommand(WindowCommand):
    def clear_view(self, view):
        if view:
            view.set_read_only(False)
            view.run_command("select_all")
            view.run_command("right_delete")
            view.set_read_only(True)
            inline.clear(self.window.active_view())

    def run(self, views=["tap", "repl"]):

        for view_name in views:
            if view_name == "repl":
                if view := state.get_active_output_view(self.window):
                    self.clear_view(view)

            elif view_name == "tap":
                if view := repl.views.tap_panel(state.get_active_output_view(self.window)):
                    self.clear_view(view)


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
        window = self.view.window()

        if scope == "ns":
            client = state.get_client(window, dialect)
            state.focus_active_runtime_view(window, dialect)
            test.run(self.view, client)
        elif scope == "var":
            region = self.view.sel()[0]
            point = region.begin()
            test_var = test.current(self.view, point)

            if test_var:
                client = state.get_client(window, dialect)
                state.focus_active_runtime_view(window, dialect)
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
    def __init__(self, window, host=None):
        self.window = window
        self.host = host

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
        if self.host is not None:
            return PortInputHandler(self.window, self.dialect)
        else:
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
        if alts := ports.discover(self.window, edn.Keyword(self.dialect)):
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
        view = self.view
        window = view.window()
        ns = namespace.name(view)

        def handler(response):
            progress.stop()
            window.status_message("[Tutkain] Evaluating view... done.")
            # Switch to current namespace after loading view
            if not response.get(edn.Keyword("exception")) and ns:
                client.switch_namespace(ns)
            client.print(response)

        progress.start("[Tutkain] Evaluating view...")

        client.backchannel.send({
            "op": edn.Keyword("load"),
            "code": base64.encode(code.encode("utf-8")),
            "file": self.view.file_name(),
        }, handler)

    def noop(*args):
        pass

    def run(self, edit, scope="outermost", code="", ns=None, ignore={"comment"}, snippet=None, inline_result=False, output="view", dialect=None):
        assert scope in {"input", "form", "ns", "innermost", "outermost", "view"}
        assert output in {"view", "clipboard"}

        point = self.view.sel()[0].begin()

        if dialect is not None:
            dialect = edn.Keyword(dialect)
        else:
            dialect = dialects.for_point(self.view, point) or edn.Keyword("clj")

        client = state.get_client(self.view.window(), dialect)

        if client is None:
            self.view.window().status_message(f"ERR: Not connected to a {dialects.name(dialect)} REPL.")
        else:
            state.focus_active_runtime_view(self.view.window(), dialect)

            if ns is not None:
                client.switch_namespace(ns)

            if scope == "input":
                auto_switch = settings.load().get("auto_switch_namespace")
                settings.load().set("auto_switch_namespace", False)

                def evaluate_input(client, code):
                    try:
                        evaluate(self.view, client, code + "\n")
                        history.update(self.view.window(), code)
                    finally:
                        settings.load().set("auto_switch_namespace", auto_switch)

                view = self.view.window().show_input_panel(
                    "Input: ",
                    history.get(self.view.window()),
                    lambda code: evaluate_input(client, code),
                    self.noop,
                    lambda: settings.load().set("auto_switch_namespace", auto_switch)
                )

                if snippet:
                    if "$FORMS" in snippet:
                        for index, region in enumerate(self.view.sel()):
                            form = forms.find_adjacent(self.view, region.begin())
                            snippet = snippet.replace(f"$FORMS[{index}]", self.view.substr(form))

                    view.run_command("insert_snippet", {"contents": snippet})

                view.settings().set("tutkain_repl_input_panel", True)
                view.settings().set("auto_complete", True)
                view.assign_syntax("Packages/Tutkain/Clojure (Tutkain).sublime-syntax")
            elif code:
                variables = {}

                for index, region in enumerate(self.view.sel()):
                    if eval_region := self.get_eval_region(region, scope, ignore):
                        variables[str(index)] = self.view.substr(eval_region)

                code = sublime.expand_variables(code, variables)
                evaluate(self.view, client, code)
            elif scope == "view":
                syntax = self.view.syntax()

                if syntax and syntax.scope not in {"source.clojure", "source.clojure.clojure-common"}:
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

                        if inline_result:
                            evaluate(self.view, client, code, eval_region.begin(), {
                                "response": {
                                    "output": edn.Keyword("inline"),
                                    "view-id": self.view.id(),
                                    "point": eval_region.end()
                                }
                            })
                        elif output == "clipboard":
                            evaluate(self.view, client, code, eval_region.begin(), {
                                "response": {
                                    "output": edn.Keyword("clipboard")
                                }
                            })
                        else:
                            evaluate(self.view, client, code, eval_region.begin())

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
    def choose_build_id(self, view, ids, on_done):
        if items := list(map(lambda id: id.name, ids)):
            self.window.show_quick_panel(
                items,
                lambda index: view.close() if index == -1 else on_done(index),
                placeholder="Choose shadow-cljs build ID",
                flags=sublime.MONOSPACE_FONT
            )

    def connect(self, dialect, host, port, view, output, backchannel, build_id):
        if dialect == edn.Keyword("cljs"):
            if not backchannel:
                sublime.error_message("[Tutkain]: The backchannel: false argument to tutkain_connect is currently not supported for ClojureScript.")
            else:
                client = repl.JSClient(
                    host,
                    port,
                    options={
                        "build_id": build_id,
                        "prompt_for_build_id": lambda ids, on_done: self.choose_build_id(view, ids, on_done),
                        "backchannel": settings.backchannel_options(dialect, backchannel)
                    }
                )
        elif dialect == edn.Keyword("bb"):
            client = repl.BabashkaClient(host, port)
        else:
            client = repl.JVMClient(
                host,
                port,
                options={"backchannel": settings.backchannel_options(dialect, backchannel)}
            )

        repl.start(view, client)
        repl.start_printer(client, view)

    def run(self, dialect, host, port, view_id=None, output="view", backchannel=True, build_id=None):
        active_view = self.window.active_view()
        output_view = repl.views.get_or_create_view(self.window, output, view_id)

        try:
            self.connect(
                edn.Keyword(dialect),
                host,
                int(port),
                output_view,
                output,
                backchannel,
                edn.Keyword(build_id) if build_id else None
            )
        except ConnectionRefusedError:
            output_view.close()
            self.window.status_message(f"ERR: connection to {host}:{port} refused.")
        finally:
            self.window.focus_view(active_view)

    def input(self, args):
        if "dialect" in args and "host" in args and "port" in args:
            return None
        elif "dialect" in args and "host" in args:
            return PortInputHandler(self.window, args["dialect"])
        elif "dialect" in args:
            return HostInputHandler(self.window, args["dialect"])
        elif "host" in args:
            return DialectInputHandler(self.window, host=args["host"])
        else:
            return DialectInputHandler(self.window)


class TutkainDisconnectCommand(WindowCommand):
    def run(self):
        repl.stop(self.window)


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


class TutkainShowPopupCommand(TextCommand):
    def run(self, _, item={}):
        info.show_popup(self.view, -1, {edn.Keyword("info"): edn.kwmap(item)})


def lookup(view, form, handler):
    if not view.settings().get("tutkain_repl_view_dialect") and form and (
        dialect := dialects.for_point(view, form.begin())
    ) and (
        client := state.get_client(view.window(), dialect)
    ):
        client.backchannel.send({
            "op": edn.Keyword("lookup"),
            "ident": view.substr(form),
            "ns": namespace.name(view),
            "dialect": dialect
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

        if form:
            # Ugly hack: for e.g. #'foo/bar, forms.find_adjacent returns the
            # whole thing, when here we actually want just foo/bar.
            form = selectors.filter_region(self.view, form, selector)
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
    for view in filter(repl.views.get_dialect, vs):
        dialect = repl.views.get_dialect(view)
        host = repl.views.get_host(view)
        port = repl.views.get_port(view)

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

    def on_selection_modified_async(self, view):
        if settings.load().get("highlight_locals", True) and (sel := view.sel()):
            try:
                point = sel[0].begin()

                if symbol := symbol_at_point(view, point):
                    fetch_locals(view, point, symbol, partial(add_local_regions, view))
                else:
                    view.erase_regions("tutkain_locals")
            except IndexError:
                # IndexError can happen if the view closes before we try getting the index on sel
                pass

    def on_deactivated_async(self, view):
        inline.clear(view)

    def on_activated(self, view):
        if client_id := repl.views.get_client_id(view):
            state.set_active_connection(view.window(), state.get_connection_by_id(client_id))
        else:
            state.on_activated(view.window(), view)

    def on_hover(self, view, point, hover_zone):
        if settings.load().get("lookup_on_hover") and view.match_selector(
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
        if connection := state.get_connection_by_id(repl.views.get_client_id(view)):
            connection.client.halt()

    def on_query_completions(self, view, prefix, locations):
        if settings.load().get("auto_complete"):
            point = locations[0] - 1
            return completions.get_completions(view, prefix, point)

    def on_pre_close_project(self, window):
        repl.stop(window)


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
        client = state.get_client(self.window, dialect)

        if client is None:
            self.window.status_message("ERR: Not connected to a REPL.")
        else:
            state.focus_active_runtime_view(self.window, dialect)
            client.backchannel.send({"op": edn.Keyword("interrupt")})


class TutkainInsertNewlineCommand(TextCommand):
    def run(self, edit, extend_comment=True):
        indent.insert_newline_and_indent(self.view, edit, extend_comment)


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
        self.view.settings().erase(test.RESULTS_SETTINGS_KEY)


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
        view.assign_syntax("Packages/Tutkain/Clojure (Tutkain).sublime-syntax")
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

    def result_line(self, result):
        begin, _ = result["region"]

        return self.view.rowcol(begin)[0] + 1

    def result_quick_panel_item(self, result):
        trigger = result["name"]
        details = f"Line {self.result_line(result)}"

        annotation_kind = None

        # We use a custom kind for errors and failures.
        # https://www.sublimetext.com/docs/api_reference.html#type-kind_info

        if result["type"] == "fail":
            annotation_kind = ("Fail", (sublime.KIND_ID_COLOR_REDISH, "F", ""))
        elif result["type"] == "error":
            annotation_kind = ("Error", (sublime.KIND_ID_COLOR_YELLOWISH, "E", ""))
        else:
            annotation_kind = (str(result["type"]), sublime.KIND_AMBIGUOUS)

        annotation, kind = annotation_kind

        return sublime.QuickPanelItem(trigger, details, annotation, kind)

    def run(self, _):
        view = self.view

        if unsuccessful := test.unsuccessful(view):

            def goto(i):
                if i != -1:
                    begin, _ = unsuccessful[i]["region"]

                    line, column = view.rowcol(begin)

                    file_name_encoded_position = f"{view.file_name()}:{line+1}:{column}"

                    # sublime.ENCODED_POSITION: Indicates the file_name should be searched for a :row or :row:col suffix
                    # See https://www.sublimetext.com/docs/api_reference.html#sublime.Window
                    view.window().open_file(file_name_encoded_position, flags=sublime.ENCODED_POSITION)

            items = [self.result_quick_panel_item(result) for result in unsuccessful]

            view.window().show_quick_panel(
                items,
                goto,
                on_highlight=goto
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
        client := state.get_client(view.window(), dialect)
    ) and (
        "analyzer.clj" in client.capabilities
    ) and (
        outermost := sexp.outermost(view, point, edge=False, ignore={"comment"})
    ):
        line, column = view.rowcol(form.begin())
        end_column = column + form.size()
        start_line, start_column = view.rowcol(outermost.open.region.begin())
        context = view.substr(outermost.extent())

        if local := view.substr(form).strip():
            client.backchannel.send({
                "op": edn.Keyword("locals"),
                "dialect": dialect,
                "file": view.file_name() or "NO_SOURCE_FILE",
                "ns": namespace.name(view),
                "context": base64.encode(context.encode("utf-8")),
                "form": local,
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


class TutkainSelectLocalsCommand(TextCommand):
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


class TutkainAproposCommand(WindowCommand):
    def send_request(self, client, pattern):
        client.backchannel.send({
            "op": edn.Keyword("apropos"),
            "pattern": pattern
        }, handler=lambda response: query.handle_response(self.window, completions.KINDS, response))

    def run(self, pattern=None):
        dialect = edn.Keyword("clj")

        if client := state.get_client(self.window, dialect):
            if pattern is None:
                panel = self.window.show_input_panel(
                    "Apropos",
                    "",
                    lambda pattern: self.send_request(client, pattern),
                    lambda _: None,
                    lambda: None,
                )

                panel.assign_syntax("Packages/Regular Expressions/RegExp.sublime-syntax")
            else:
                self.send_request(client, pattern)
        else:
            self.window.status_message(f"ERR: Not connected to a {dialects.name(dialect)} REPL.")


class TutkainDirCommand(TextCommand):
    def run(self, _):
        window = self.view.window()
        dialect = dialects.for_view(self.view)

        if client := state.get_client(window, dialect):
            if sel := self.view.sel():
                point = sel[0].begin()

                if symbol := selectors.expand_by_selector(self.view, point, "meta.symbol"):
                    client.backchannel.send({
                        "op": edn.Keyword("dir"),
                        "ns": namespace.name(self.view),
                        "sym": self.view.substr(symbol)
                    }, lambda response: query.handle_response(window, completions.KINDS, response))
        else:
            self.view.window().status_message(f"ERR: Not connected to a {dialects.name(dialect)} REPL.")


class TutkainLoadedLibsCommand(TextCommand):
    def run(self, _):
        window = self.view.window()
        dialect = dialects.for_view(self.view) or edn.Keyword("clj")

        if client := state.get_client(window, dialect):
            client.backchannel.send({
                "op": edn.Keyword("loaded-libs"),
                "dialect": dialect
            }, lambda response: query.handle_response(window, completions.KINDS, response))
        else:
            self.view.window().status_message(f"ERR: Not connected to a {dialects.name(dialect)} REPL.")


class TutkainExploreStackTraceCommand(TextCommand):
    def goto(self, elements, index):
        if index == -1 and (window := self.view.window()):
            window.focus_view(self.view)
        else:
            location = info.parse_location(elements[index])
            info.goto(self.view.window(), location, flags=sublime.ENCODED_POSITION | sublime.TRANSIENT)

    def handler(self, response):
        if elements := response.get(edn.Keyword("stacktrace")):
            items = []

            for element in elements:
                trigger = element.get(edn.Keyword("name"))
                filename = element.get(edn.Keyword("file-name"))
                line = element.get(edn.Keyword("line"))
                items.append(
                    sublime.QuickPanelItem(
                        trigger,
                        annotation=f"{filename}:{line}",
                        kind=sublime.KIND_FUNCTION
                    )
                )

            self.view.window().show_quick_panel(
                items,
                lambda index: self.goto(elements, index),
                on_highlight=lambda index: self.goto(elements, index)
            )

    def run(self, _):
        if client := state.get_client(self.view.window(), edn.Keyword("clj")):
            client.backchannel.send({
                "op": edn.Keyword("resolve-stacktrace")
            }, self.handler)


class TutkainPromptCommand(WindowCommand):
    def on_done(self, client, code):
        if code:
            client.evaluate(code, {"file": "NO_SOURCE_FILE"})
            history.update(self.window, code)

        settings.load().set("auto_switch_namespace", self.auto_switch)
        self.prompt(client)

    def on_change(self, _):
        None

    def on_cancel(self):
        settings.load().set("auto_switch_namespace", self.auto_switch)

    def prompt(self, client):
        settings.load().set("auto_switch_namespace", False)

        view = self.window.show_input_panel(
            "Input: ",
            history.get(self.window),
            lambda code: self.on_done(client, code),
            self.on_change,
            self.on_cancel
        )

        view.settings().set("tutkain_repl_input_panel", True)

    def run(self):
        if client := state.get_client(self.window, edn.Keyword("clj")):
            self.auto_switch = settings.load().get("auto_switch_namespace")
            self.prompt(client)
        else:
            self.window.status_message("ERR: Not connected to a REPL.")


class TutkainToggleAutoSwitchNamespaceCommand(TextCommand):
    def run(self, _):
        s = settings.load()
        current = s.get("auto_switch_namespace")
        s.set("auto_switch_namespace", not current)

        if s.get("auto_switch_namespace"):
            window = self.view.window()
            window.status_message(f"[⏽] [Tutkain] Automatic namespace switching enabled.")

            if (sel := self.view.sel()) and (
                dialect := dialects.for_point(self.view, sel[0].begin())
            ) and (
                client := state.get_client(window, dialect)
            ) and (ns := namespace.name(self.view) or namespace.default(dialect)):
                client.switch_namespace(ns)
        else:
            self.view.window().status_message(f"[⭘] [Tutkain] Automatic namespace switching disabled.")


class ClientIdInputHandler(ListInputHandler):
    def placeholder(self):
        return "Choose connected runtime to activate"

    def make_item(self, connection):
        if connection.view.element() is None:
            output = "view"
        else:
            output = "panel"

        annotation = f"{dialects.name(connection.client.dialect)} ({output})"
        text = f"{connection.client.host}:{connection.client.port}"
        return sublime.ListInputItem(text, connection.client.id, annotation=annotation)

    def list_items(self):
        return list(map(self.make_item, list(state.get_connections().values())))


class TutkainChooseActiveRuntimeCommand(WindowCommand):
    def input(self, args):
        return ClientIdInputHandler()

    def run(self, client_id):
        state.set_active_connection(self.window, state.get_connection_by_id(client_id))
