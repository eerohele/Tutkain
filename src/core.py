import json
import os
import textwrap
from functools import partial

import sublime
from sublime_plugin import (
    EventListener,
    ListInputHandler,
    TextCommand,
    TextInputHandler,
    ViewEventListener,
    WindowCommand,
)

from ..api import edn
from . import (
    base64,
    clojuredocs,
    completions,
    dialects,
    forms,
    indent,
    inline,
    namespace,
    paredit,
    progress,
    repl,
    selectors,
    settings,
    sexp,
    state,
    temp,
    test,
)
from .log import start_logging, stop_logging
from .repl import history, info, ports, query


def make_color_scheme(cache_dir):
    """
    Add the tutkain.repl.stderr scope into the current color scheme.

    We want stderr messages in the same REPL output view as evaluation results, but we don't
    want them to use syntax highlighting. We therefore have to resort to this awful hack where
    every time the plugin is loaded or the color scheme changes, we generate a new color scheme in
    the Sublime Text cache directory. That color scheme defines the tutkain.repl.stderr scope which
    has an almost-transparent background color, creating the illusion that we're only setting the
    foreground color of the text.
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


def dissoc(d, ks):
    return {k: d[k] for k in set(list(d.keys())) - ks}


class TemporaryFileEventListener(ViewEventListener):
    @classmethod
    def is_applicable(_, settings):
        return settings.has("tutkain_temp_file")

    def on_load_async(self):
        try:
            if temp_file := self.view.settings().get("tutkain_temp_file"):
                path = temp_file.get("path")
                descriptor = temp_file.get("descriptor")

                if name := temp_file.get("name"):
                    self.view.set_name(name)

                if temp_file.get("selection") == "end":
                    self.view.sel().clear()
                    self.view.sel().add(
                        sublime.Region(self.view.size(), self.view.size())
                    )

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
            state.reset_gutter_markers(view)

    def run(self, views=["tap", "repl"]):
        for view_name in views:
            if view_name == "repl":
                if view := state.get_active_output_view(self.window):
                    self.clear_view(view)

            elif view_name == "tap":
                if view := repl.views.tap_panel(
                    state.get_active_output_view(self.window)
                ):
                    self.clear_view(view)


class TutkainEvaluateFormCommand(TextCommand):
    def run(self, _, scope="outermost", ignore={"comment"}, inline_result=False):
        self.view.window().status_message(
            "tutkain_evaluate_form is deprecated; use tutkain_evaluate instead"
        )

        self.view.run_command(
            "tutkain_evaluate",
            {"scope": scope, "ignore": ignore, "inline_result": inline_result},
        )


class TutkainEvaluateViewCommand(TextCommand):
    def run(self, _):
        self.view.window().status_message(
            "tutkain_evaluate_view is deprecated; use tutkain_evaluate instead"
        )


class TutkainRunTests(TextCommand):
    def run(self, _, scope="ns"):
        dialect = dialects.for_view(self.view)
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
            sublime.ListInputItem(
                "Var",
                "var",
                details="Run the test defined by the var under the caret.",
                annotation="<code>deftest</code>",
            ),
            sublime.ListInputItem(
                "Namespace", "ns", details="Run all tests in the current namespace."
            ),
        ]


class TutkainRunTestsInCurrentNamespaceCommand(TextCommand):
    def run(self, edit):
        self.view.window().status_message(
            "tutkain_run_tests_in_current_namespace is deprecated; use tutkain_run_tests instead"
        )
        self.view.run_command("tutkain_run_tests", {"scope": "ns"})


class TutkainRunTestUnderCursorCommand(TextCommand):
    def run(self, edit):
        self.view.window().status_message(
            "tutkain_run_test_under_cursor is deprecated; use tutkain_run_tests instead"
        )
        self.view.run_command("tutkain_run_tests", {"scope": "var"})


class DialectInputHandler(ListInputHandler):
    def __init__(self, window, host=None):
        self.window = window
        self.host = host

    def placeholder(self):
        return "Choose dialect"

    def list_items(self):
        return [
            sublime.ListInputItem(
                "Clojure",
                "clj",
                details="A dynamic and functional Lisp that runs on the Java Virtual Machine.",
            ),
            sublime.ListInputItem(
                "ClojureScript",
                "cljs",
                annotation="shadow-cljs only",
                details="A compiler for Clojure that targets JavaScript.",
            ),
            sublime.ListInputItem(
                "Babashka", "bb", details="A fast, native Clojure scripting runtime."
            ),
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
        if self.dialect == "bb":
            return "1666"
        elif alts := ports.discover(self.window, edn.Keyword(self.dialect)):
            return alts[0][1]
        else:
            return ""


class TutkainEvaluateInputCommand(WindowCommand):
    def run(self):
        self.window.status_message(
            "tutkain_evaluate_input is deprecated; use tutkain_evaluate instead"
        )
        self.window.active_view().run_command("tutkain_evaluate", {"scope": "input"})


def without_discard_macro(view, region):
    if region:
        s = sublime.Region(region.begin(), region.begin() + 2)

        if view.substr(s) == "#_":
            return sublime.Region(s.end(), region.end())

    return region


def get_eval_region(view, region, scope="outermost", ignore={}):
    eval_region = region

    if not eval_region.empty():
        return eval_region
    elif scope == "form":
        eval_region = forms.find_adjacent(view, region.begin())
    elif scope == "innermost" and (
        innermost := sexp.innermost(view, region.begin(), edge=True)
    ):
        eval_region = innermost.extent()
    elif scope == "outermost" and (
        outermost := sexp.outermost(view, region.begin(), ignore=ignore)
    ):
        eval_region = outermost.extent()

    return without_discard_macro(view, eval_region)


class TutkainReplaceRegionImplCommand(TextCommand):
    def run(self, edit, region=None, string=None):
        if region and string:
            region = sublime.Region(region[0], region[1])
            self.view.replace(edit, region, string)


class TutkainEvaluateCommand(TextCommand):
    def make_options(self, options, point, dialect, auto_switch_namespace):
        if not options.get("file") and (file_name := self.view.file_name()):
            options["file"] = file_name

        if not options.get("file"):
            options["file"] = "NO_SOURCE_FILE"

        if not options.get("ns"):
            if auto_switch_namespace:
                ns = namespace.name_or_default(self.view, dialect)
                options["ns"] = edn.Symbol(ns)

        line, column = self.view.rowcol(point)

        options["line"] = line + 1
        options["column"] = column + 1

        return options

    def eval(
        self,
        client,
        code,
        auto_switch_namespace,
        handler=None,
        point=0,
        options={},
    ):
        opts = self.make_options(options, point, client.dialect, auto_switch_namespace)

        if code and (code := indent.reindent(code, opts.get("column", 1))):
            client.print(edn.kwmap({"tag": edn.Keyword("in"), "val": code + "\n"}))

            mode = opts.get("mode")
            opts = dissoc(opts, {"mode"})

            if mode == "rpc":
                client.evaluate_rpc(code, handler, opts)
            else:
                client.evaluate_repl(code, opts)

    def get_dialect(self, dialect, point):
        if dialect is not None:
            return edn.Keyword(dialect)
        else:
            return dialects.for_point(self.view, point) or edn.Keyword("clj")

    def noop(*args):
        pass

    def run(
        self,
        _,
        scope="outermost",
        code="",
        ns=None,
        ignore={"comment"},
        snippet=None,
        inline_result=False,
        output=None,
        dialect=None,
        mode=None,
        # Undocumented and unsupported; for testing only, currently
        auto_switch_namespace=None,
    ):
        assert scope in {
            "input",
            "form",
            "ns",
            "innermost",
            "outermost",
            "view",
            "up_to_point",
        }
        assert output in {None, "selection", "clipboard", "inline"}

        if sel := self.view.sel():
            current_region = sel[0]
        else:
            current_region = sublime.Region(0, 0)

        dialect = self.get_dialect(dialect, current_region.begin())
        client = state.get_client(self.view.window(), dialect)

        if client is None:
            self.view.window().status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )
        else:
            if auto_switch_namespace is None:
                auto_switch_namespace = settings.load().get(
                    "auto_switch_namespace", True
                )

            if inline_result:
                self.view.window().status_message(
                    """inline_result is deprecated; use "output": "inline" instead"""
                )

                output = "inline"

            # Force RPC evaluation mode if client is in RPC mode and for inline, clipboard, and selection outputs
            if client.mode == "rpc" or output in {"inline", "clipboard", "selection"}:
                options = {"mode": "rpc"}
            else:
                options = {"mode": mode or client.mode}

            if scope == "view":
                syntax = self.view.syntax()

                if syntax and syntax.scope not in {
                    "source.clojure",
                    "source.clojure.clojure-common",
                    "source.clojure.babashka",
                }:
                    self.view.window().status_message(
                        "Active view has incompatible syntax; can't evaluate."
                    )
                else:
                    eval_region = sublime.Region(0, self.view.size())

                    if not eval_region.empty():
                        window = self.view.window()

                        def handler(response):
                            progress.stop()
                            window.status_message("✓ Evaluating view... done.")

                            if edn.Keyword("exception") in response:
                                client.print(response)
                                window.status_message(
                                    "⚠ Could not evaluate view; see output view for more information."
                                )

                        progress.start("Evaluating view...")

                        code = self.view.substr(eval_region)

                        client.send_op(
                            {
                                "op": edn.Keyword("load"),
                                "code": base64.encode(code.encode("utf-8")),
                                "file": self.view.file_name(),
                            },
                            handler,
                        )
            else:
                if output == "clipboard":

                    def handler(item):
                        val = item.get(edn.Keyword("val"))
                        val = val[:-1] if val[-1] == "\n" else val
                        sublime.set_clipboard(val)
                        client.print(item)

                        sublime.active_window().status_message(
                            "[Tutkain] Evaluation result copied to clipboard."
                        )

                    def evaluator(region, code, options, sel=None):
                        self.eval(
                            client,
                            code,
                            auto_switch_namespace,
                            handler=handler,
                            point=region.begin(),
                            options=options,
                        )

                elif output == "inline":

                    def handler(point, item):
                        client.print(item)

                        inline.clear(self.view)

                        inline.show(
                            self.view,
                            point,
                            item.get(edn.Keyword("val")),
                        )

                    def evaluator(region, code, options, sel=None):
                        self.eval(
                            client,
                            code,
                            auto_switch_namespace,
                            handler=lambda item: handler(region.end(), item),
                            point=region.begin(),
                            options=options,
                        )

                elif output == "selection":

                    def handler(region, item):
                        val = item.get(edn.Keyword("val"))
                        val = val[:-1] if val[-1] == "\n" else val

                        self.view.run_command(
                            "tutkain_replace_region_impl",
                            {"region": region.to_tuple(), "string": val},
                        )

                        client.print(item)

                    def evaluator(region, code, options, sel=None):
                        self.eval(
                            client,
                            code,
                            auto_switch_namespace,
                            handler=lambda item: handler(region, item),
                            point=region.begin(),
                            options=options,
                        )

                else:

                    def evaluator(region, code, options, sel=None):
                        self.eval(
                            client,
                            code,
                            auto_switch_namespace,
                            point=region.begin(),
                            options=options,
                        )

                # FIXME: Support output with any scope
                state.focus_active_runtime_view(self.view.window(), dialect)

                if scope == "mark" and (
                    mark := self.view.window().settings().get("tutkain_mark")
                ):
                    options = {**options, **mark["options"]}

                    if "ns" in options:
                        options["ns"] = edn.Symbol(options["ns"])

                    region = options["region"]
                    region = sublime.Region(region[0], region[1])
                    del options["region"]
                    evaluator(region, mark["code"], options)

                elif scope == "input":

                    def evaluate_input(client, code):
                        options["file"] = self.view.file_name()
                        evaluator(sublime.Region(1, 1), code, options)
                        history.update(self.view.window(), code)

                    view = self.view.window().show_input_panel(
                        "Input: ",
                        history.get(self.view.window()),
                        lambda code: evaluate_input(client, code),
                        self.noop,
                        self.noop,
                    )

                    if snippet:
                        if "$FORMS" in snippet:
                            for index, region in enumerate(self.view.sel()):
                                form = forms.find_adjacent(self.view, region.begin())
                                snippet = snippet.replace(
                                    f"$FORMS[{index}]", self.view.substr(form)
                                )

                        view.run_command("insert_snippet", {"contents": snippet})

                    view.settings().set("tutkain_repl_input_panel", True)
                    view.settings().set("auto_complete", True)
                    view.assign_syntax(
                        "Packages/Tutkain/Clojure (Tutkain).sublime-syntax"
                    )

                elif scope == "up_to_point":
                    for region in self.view.sel():
                        if innermost := sexp.innermost(
                            self.view, region.end(), edge=False
                        ):
                            region_up_to_point = sublime.Region(
                                innermost.open.region.begin(), region.end()
                            )
                            code = self.view.substr(
                                region_up_to_point
                            ) + self.view.substr(innermost.close.region)

                            self.eval(
                                client,
                                code,
                                auto_switch_namespace,
                                point=region.end(),
                                options=options,
                            )
                        else:
                            # Stop at the first point that has a non-Clojure scope
                            # (presumably when within a Markdown code block), or
                            # at 0 if not found.
                            begin = max(
                                (
                                    selectors.find(
                                        self.view,
                                        region.begin(),
                                        "-source.clojure",
                                        forward=False,
                                    )
                                    or 0
                                )
                                + 1,
                                0,
                            )
                            code = self.view.substr(sublime.Region(begin, region.end()))
                            self.eval(
                                client,
                                code,
                                auto_switch_namespace,
                                point=region.end(),
                                options=options,
                            )

                elif scope == "ns":
                    ns_forms = namespace.forms(self.view)

                    for region in ns_forms:
                        code = self.view.substr(region)
                        evaluator(region, code, options)
                elif code:
                    variables = {}

                    if ns:
                        options["ns"] = edn.Symbol(ns)
                    elif auto_switch_namespace:
                        ns = namespace.name_or_default(self.view, dialect)
                        options["ns"] = edn.Symbol(ns)

                    if ns:
                        variables["ns"] = ns

                    if file_name := self.view.file_name():
                        variables["file"] = file_name

                    for index, region in enumerate(self.view.sel()):
                        if eval_region := get_eval_region(
                            self.view, region, scope, ignore
                        ):
                            variables[str(index)] = self.view.substr(eval_region)

                    code = sublime.expand_variables(code, variables)
                    evaluator(current_region, code, options)
                else:
                    # With selection outputs, we have to handle the selections
                    # in reverse to account for replacing multiple regions.
                    #
                    # Could probably reverse for every output type, but would
                    # have to update all tests for that.
                    if output == "selection":
                        sels = reversed(self.view.sel())
                    else:
                        sels = self.view.sel()

                    for sel in sels:
                        eval_region = get_eval_region(self.view, sel, scope, ignore)

                        if not eval_region.empty():
                            code = self.view.substr(eval_region)
                            evaluator(eval_region, code, options, sel=sel)

    def input(self, args):
        if any(map(lambda region: not region.empty(), self.view.sel())):
            return None
        elif "code" in args or "scope" in args:
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
            sublime.ListInputItem(
                "Adjacent Form",
                "form",
                details="The form (not necessarily S-expression) adjacent to the caret.",
            ),
            sublime.ListInputItem(
                "Innermost S-expression",
                "innermost",
                details="The innermost S-expression with respect to the caret position.",
            ),
            sublime.ListInputItem(
                "Outermost S-expression",
                "outermost",
                details="The outermost S-expression with respect to the caret position.",
                annotation="ignores (comment)",
            ),
            sublime.ListInputItem(
                "Up to Point",
                "up_to_point",
                details="Up to the caret position within the innermost S-expression, or, if not within an S-expression, in the current view.",
            ),
            sublime.ListInputItem(
                "Mark", "mark", details="The form marked via Tutkain: Mark."
            ),
            sublime.ListInputItem(
                "Active View",
                "view",
                details="The entire contents of the currently active view.",
            ),
            sublime.ListInputItem(
                "Input", "input", details="Tutkain prompts you for input to evaluate."
            ),
            sublime.ListInputItem(
                "Namespace Declarations",
                "ns",
                details="Every namespace declaration (<code>ns</code> form) in the active view.",
            ),
        ]


class TutkainConnectCommand(WindowCommand):
    def choose_build_id(self, view, ids, on_done):
        if items := list(map(lambda id: id.name, ids)):
            self.window.show_quick_panel(
                items,
                lambda index: view.close() if index == -1 else on_done(index),
                placeholder="Choose shadow-cljs build ID",
                flags=sublime.MONOSPACE_FONT,
            )

    def connect(
        self, dialect, host, port, view, output, backchannel, build_id, init, mode
    ):
        backchannel_options = repl.backchannel_options(
            self.window.project_data(), dialect, backchannel
        )

        tap_panel = settings.load().get("tap_panel", False)

        if dialect == edn.Keyword("cljs"):
            client = repl.JSClient(
                host,
                port,
                options={
                    "build_id": build_id,
                    "prompt_for_build_id": lambda ids, on_done: self.choose_build_id(
                        view, ids, on_done
                    ),
                    "add_tap": tap_panel,
                },
            )

            repl.start(view, client)
            repl.start_printer(client, view)
        elif dialect == edn.Keyword("bb"):
            client = repl.BabashkaClient(
                host,
                port,
                mode,
                options={
                    "init": init,
                    "backchannel": backchannel_options,
                    "add_tap": tap_panel,
                },
            )

            repl.start(view, client)
            repl.start_printer(client, view)
        else:
            client = repl.JVMClient(
                host,
                port,
                mode,
                options={
                    "init": init,
                    "backchannel": backchannel_options,
                    "add_tap": tap_panel,
                },
            )

            repl.start(view, client)
            repl.start_printer(client, view)

    def run(
        self,
        dialect,
        host,
        port,
        view_id=None,
        output="panel",
        backchannel=True,
        build_id=None,
        init=None,
        mode=None,
    ):
        mode = mode or settings.load().get("default_connection_mode")
        active_view = self.window.active_view()
        output_view = repl.views.get_or_create_view(self.window, output, view_id)
        dialect = edn.Keyword(dialect)

        if port := ports.parse(self.window, port, dialect, ports.discover):
            try:
                self.connect(
                    dialect,
                    host,
                    port,
                    output_view,
                    output,
                    backchannel,
                    edn.Keyword(build_id) if build_id else None,
                    init,
                    mode,
                )
            except ConnectionRefusedError:
                output_view.close()
                self.window.status_message(f"⚠ connection to {host}:{port} refused.")
            finally:
                self.window.focus_view(active_view)
        else:
            self.window.status_message("⚠ No REPL port file found.")

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
        "ClojureScript": "Packages/Tutkain/ClojureScript (Tutkain).sublime-syntax",
        "Babashka": "Packages/Tutkain/Babashka (Tutkain).sublime-syntax",
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
            placeholder="Choose syntax",
        )


class TutkainShowPopupCommand(TextCommand):
    def run(self, _, item={}):
        info.show_popup(self.view, -1, {edn.Keyword("info"): edn.kwmap(item)})


def lookup(view, form, handler):
    if (
        not view.settings().get("tutkain_repl_view_dialect")
        and form
        and (dialect := dialects.for_point(view, form.begin()))
        and (client := state.get_client(view.window(), dialect))
    ):
        client.send_op(
            {
                "op": edn.Keyword("lookup"),
                "ident": view.substr(form),
                "ns": namespace.name(view),
                "dialect": dialect,
            },
            handler,
        )


class TutkainShowInformationCommand(TextCommand):
    def handler(self, form, response):
        info.show_popup(self.view, form.begin(), response)

    def predicate(self, selector, form):
        return self.view.match_selector(form.begin(), selector)

    def run(
        self,
        _,
        selector="meta.symbol | constant.other.keyword.qualified | constant.other.keyword.auto-qualified",
        seek_backward=False,
    ):
        start_point = self.view.sel()[0].begin()

        if seek_backward:
            form = forms.seek_backward(
                self.view, start_point, lambda form: self.predicate(selector, form)
            )
        else:
            form = forms.find_adjacent(self.view, start_point)

        if form:
            # Ugly hack: for e.g. #'foo/bar, forms.find_adjacent returns the
            # whole thing, when here we actually want just foo/bar.
            form = selectors.filter_region(self.view, form, selector)
            lookup(self.view, form, lambda response: self.handler(form, response))


class TutkainGotoDefinitionCommand(TextCommand):
    def handler(self, response):
        info.goto(
            self.view.window(), info.parse_location(response.get(edn.Keyword("info")))
        )

    def run(self, _):
        point = self.view.sel()[0].begin()
        form = selectors.expand_by_selector(self.view, point, "meta.symbol")
        lookup(self.view, form, self.handler)


# DEPRECATED
class TutkainShowSymbolInformationCommand(TextCommand):
    def handler(self, form, response):
        info.show_popup(self.view, form.begin(), response)

    def run(self, _):
        self.view.window().status_message(
            "tutkain_show_symbol_information is deprecated; use tutkain_show_information instead"
        )
        point = self.view.sel()[0].begin()
        form = selectors.expand_by_selector(
            self.view,
            point,
            "meta.symbol | constant.other.keyword.qualified | constant.other.keyword.auto-qualified",
        )
        lookup(self.view, form, lambda response: self.handler(form, response))


# DEPRECATED
class TutkainGotoSymbolDefinitionCommand(TextCommand):
    def handler(self, response):
        info.goto(
            self.view.window(), info.parse_location(response.get(edn.Keyword("info")))
        )

    def run(self, _):
        self.view.window().status_message(
            "tutkain_goto_symbol_definition is deprecated; use tutkain_goto_definition instead"
        )
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
                "tutkain_connect",
                {
                    "dialect": dialect.name,
                    "host": host,
                    "port": port,
                    "view_id": view.id(),
                },
            )


def add_local_regions(view, tuples):
    """Given a set of tuples containing the begin and end point of a Region,
    add a region for each local symbol delimited by the points."""
    if regions := [sublime.Region(begin, end) for begin, end in tuples]:
        view.add_regions(
            "tutkain_locals",
            regions,
            "region.cyanish",
            flags=sublime.DRAW_SOLID_UNDERLINE
            | sublime.DRAW_NO_FILL
            | sublime.DRAW_NO_OUTLINE,
        )


def symbol_at_point(view, point):
    """Given a view and a point, return the Clojure symbol at the point."""
    if view.match_selector(
        point,
        "meta.symbol - (meta.special-form | variable.function | keyword.declaration.function)",
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
            state.set_active_connection(
                view.window(), state.get_connection_by_id(client_id)
            )
        else:
            state.on_activated(view.window(), view)

    def on_hover(self, view, point, hover_zone):
        if settings.load().get("lookup_on_hover") and view.match_selector(
            point,
            "source.clojure & (meta.symbol | constant.other.keyword.qualified | constant.other.keyword.auto-qualified)",
        ):
            form = forms.find_adjacent(view, point)
            lookup(view, form, lambda response: info.show_popup(view, point, response))

    def on_close(self, view):
        if view.settings().get("tutkain_repl_view_dialect"):
            window = sublime.active_window()
            num_groups = window.num_groups()

            if num_groups == 2 and len(window.views_in_group(num_groups - 1)) == 0:
                window.set_layout(
                    {"cells": [[0, 0, 1, 1]], "cols": [0.0, 1.0], "rows": [0.0, 1.0]}
                )

    def on_pre_close(self, view):
        if connection := state.get_connection_by_id(repl.views.get_client_id(view)):
            connection.client.halt()

    def on_query_completions(self, view, prefix, locations):
        if settings.load().get("auto_complete"):
            point = locations[0] - 1
            return completions.get_completions(view, prefix, point)

    def on_pre_close_project(self, window):
        repl.stop(window)

    def on_post_text_command(self, view, command_name, _):
        if view.settings().has("tutkain_repl_client_id"):
            if command_name == "copy":
                text = str(sublime.get_clipboard()).replace("\u2063", "")
                sublime.set_clipboard(text)


class TutkainExpandSelectionImplCommand(TextCommand):
    """Internal, do not use. Use the tutkain_expand_selection command instead."""

    def run(self, _, region=None):
        region = sublime.Region(region[0], region[1])
        self.expand(region)

    def expand(self, region):
        if region == sublime.Region(0, self.view.size()):
            pass
        elif not region.empty() and self.view.match_selector(
            region.end(), "-meta.sexp"
        ):
            self.view.sel().add(sublime.Region(0, self.view.size()))
        elif (
            region.empty()
            and self.view.match_selector(
                region.begin(), "meta.tagged-element.element meta.tagged-element.tag"
            )
            and (element := forms.find_next(self.view, region.begin()))
        ):
            tag = selectors.expand_by_selector(
                self.view, region.begin(), "meta.tagged-element.tag"
            )
            self.view.sel().add(sublime.Region(tag.begin(), element.end() - 1))
        elif (
            region.empty()
            and self.view.match_selector(region.begin(), "meta.tagged-element.element")
            and (form := forms.find_adjacent(self.view, region.begin()))
        ):
            self.view.sel().add(form)
        elif (
            region.empty()
            and self.view.match_selector(region.begin(), "meta.tagged-element.tag")
            and (form := forms.find_adjacent(self.view, region.begin()))
        ):
            self.view.sel().add(form)
        elif region.empty() and (
            form := forms.find_adjacent(self.view, region.begin())
        ):
            self.view.sel().add(form)
        elif region.empty() and not forms.find_adjacent(self.view, region.begin()):
            self.view.run_command("expand_selection", {"to": "brackets"})
        elif (
            not region.empty()
            and self.view.match_selector(region.begin(), "meta.mapping.key")
        ) and (
            not region.empty()
            and self.view.match_selector(region.end() - 1, "meta.mapping.value")
        ):
            self.view.run_command("expand_selection", {"to": "brackets"})
        elif (
            not region.empty()
            and self.view.match_selector(region.begin(), "meta.mapping.key")
            and self.view.match_selector(region.end() - 1, "meta.mapping.key")
            and not self.view.match_selector(
                region.begin(), "meta.mapping.key meta.sexp"
            )
            and not self.view.match_selector(region.begin(), sexp.BEGIN_SELECTORS)
            and not self.view.match_selector(region.end() - 1, sexp.END_SELECTORS)
        ):
            value_begin = selectors.find(
                self.view,
                region.end(),
                "meta.mapping.value",
                forward=True,
                stop_at=sexp.END_SELECTORS,
            )

            if not value_begin and (
                innermost := sexp.innermost(self.view, region.begin())
            ):
                self.view.sel().add(innermost.extent())
            elif self.view.match_selector(
                value_begin, "meta.reader-form | keyword.operator.macro"
            ):
                form = forms.find_next(self.view, value_begin)
                self.view.sel().add(sublime.Region(region.begin(), form.end()))
            elif self.view.match_selector(value_begin, "meta.mapping.value meta.sexp"):
                end = sexp.innermost(self.view, value_begin).close.region.end()
                self.view.sel().add(sublime.Region(region.begin(), end))
        elif (
            not region.empty()
            and self.view.match_selector(region.begin(), sexp.BEGIN_SELECTORS)
            and self.view.match_selector(region.end() - 1, sexp.END_SELECTORS)
        ):
            self.view.run_command("expand_selection", {"to": "brackets"})

            for region in self.view.sel():
                if begin := selectors.find(
                    self.view,
                    region.begin(),
                    f"- ({sexp.ABSORB_SELECTOR})",
                    forward=False,
                    stop_at=sexp.BEGIN_SELECTORS,
                ):
                    self.view.sel().add(sublime.Region(begin + 1, region.end()))
        elif (
            not region.empty()
            and self.view.match_selector(region.begin() - 1, sexp.BEGIN_SELECTORS)
            and self.view.match_selector(region.end(), sexp.END_SELECTORS)
        ):
            innermost = sexp.innermost(self.view, region.begin(), edge=False)
            self.view.sel().add(innermost.extent())
        elif (
            not region.empty()
            and not self.view.match_selector(region.begin(), sexp.BEGIN_SELECTORS)
            and not self.view.match_selector(region.end() - 1, sexp.END_SELECTORS)
        ):
            if innermost := sexp.innermost(self.view, region.begin(), edge=False):
                if innermost.open and innermost.close:
                    self.view.sel().add(
                        sublime.Region(
                            innermost.open.region.end(), innermost.close.region.begin()
                        )
                    )
        elif (
            self.view.match_selector(region.begin(), "meta.tagged-element")
            and self.view.match_selector(region.end() - 1, "meta.tagged-element")
            and not self.view.match_selector(region.begin() - 1, "meta.tagged-element")
            and not self.view.match_selector(region.end(), "meta.tagged-element")
        ):
            if innermost := sexp.innermost(self.view, region.begin(), edge=False):
                if innermost.open and innermost.close:
                    self.view.sel().add(
                        sublime.Region(
                            innermost.open.region.end(), innermost.close.region.begin()
                        )
                    )
        elif innermost := sexp.innermost(self.view, region.begin(), edge=False):
            self.view.sel().add(innermost.extent())
        else:
            self.view.run_command("expand_selection", {"to": "brackets"})


class TutkainExpandSelectionCommand(TextCommand):
    def run(self, _):
        view = self.view

        for region in view.sel():
            if selectors.ignore(view, region.begin()):
                view.run_command("expand_selection", {"to": "scope"})
            else:
                sublime.set_timeout(
                    lambda: view.run_command(
                        "tutkain_expand_selection_impl",
                        {"region": region.to_tuple()},
                    ),
                    0,
                )


class TutkainInterruptEvaluationCommand(WindowCommand):
    def run(self):
        dialect = edn.Keyword("clj")
        client = state.get_client(self.window, dialect)

        if client is None:
            self.window.status_message("⚠ Not connected to a REPL.")
        else:
            state.focus_active_runtime_view(self.window, dialect)
            client.send_op({"op": edn.Keyword("interrupt")})


class TutkainInsertNewlineCommand(TextCommand):
    def run(self, edit, extend_comment=True):
        indent.insert_newline_and_indent(self.view, edit, extend_comment)


class TutkainIndentSexpCommand(TextCommand):
    def get_target_region(self, region, scope):
        if not region.empty():
            return region
        elif scope == "innermost" and (
            innermost := sexp.innermost(self.view, region.begin())
        ):
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
    def run(self, edit, join_on=" "):
        paredit.thread_first(self.view, edit, join_on=join_on)


class TutkainPareditThreadLastCommand(TextCommand):
    def run(self, edit, join_on=" "):
        paredit.thread_last(self.view, edit, join_on=join_on)


class TutkainPareditUnthreadCommand(TextCommand):
    def run(self, edit, join_on=" "):
        paredit.unthread(self.view, edit, join_on=join_on)


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


class TutkainPareditSplitSexpCommand(TextCommand):
    def run(self, edit):
        paredit.split_sexp(self.view, edit)


class TutkainPareditJoinSexpsCommand(TextCommand):
    def run(self, edit):
        paredit.join_sexps(self.view, edit)


class TutkainPareditRecenterOnSexpCommand(TextCommand):
    def run(self, edit):
        paredit.recenter_on_sexp(self.view, edit)


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
                    view.window().open_file(
                        file_name_encoded_position, flags=sublime.ENCODED_POSITION
                    )

            items = [self.result_quick_panel_item(result) for result in unsuccessful]

            view.window().show_quick_panel(items, goto, on_highlight=goto)


class TutkainChooseEvaluationDialectCommand(WindowCommand):
    dialects = [["clj", "Clojure"], ["cljs", "ClojureScript"], ["bb", "Babashka"]]

    def finish(self, index):
        val = self.dialects[index][0]
        self.window.settings().set("tutkain_evaluation_dialect", val)
        self.window.status_message(
            f"[Tutkain] Evaluating Clojure Common files as {dialects.name(edn.Keyword(val))}"
        )

    def run(self):
        self.window.show_quick_panel(
            self.dialects,
            self.finish,
            placeholder="Choose Clojure Common evaluation dialect",
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
        (dialect := dialects.for_point(view, point))
        and (client := state.get_client(view.window(), dialect))
        and ("analyzer.clj" in client.capabilities)
        and (outermost := sexp.outermost(view, point, edge=False, ignore={"comment"}))
    ):
        line, column = view.rowcol(form.begin())
        end_column = column + form.size()
        start_line, start_column = view.rowcol(outermost.open.region.begin())
        if extent := outermost.extent():
            if local := view.substr(form).strip():
                context = view.substr(extent)

                client.send_op(
                    {
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
                        "end-column": end_column + 1,
                    },
                    partial(handle_locals_response, view, handler),
                )


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
        self.view.run_command(
            "tutkain_add_regions", {"view_id": self.view.id(), "regions": regions}
        )

    def run(self, _):
        if sel := self.view.sel():
            point = sel[0].begin()

            if symbol := symbol_at_point(self.view, point):
                fetch_locals(self.view, point, symbol, self.handler)


class TutkainAproposCommand(WindowCommand):
    def send_request(self, client, pattern):
        client.send_op(
            {"op": edn.Keyword("apropos"), "pattern": pattern},
            handler=lambda response: query.handle_response(
                self.window, completions.KINDS, response
            ),
        )

    def run(self, pattern=None):
        dialect = dialects.for_view(self.window.active_view()) or edn.Keyword("clj")

        if client := state.get_client(self.window, dialect):
            if pattern is None:
                panel = self.window.show_input_panel(
                    "Apropos",
                    "",
                    lambda pattern: self.send_request(client, pattern),
                    lambda _: None,
                    lambda: None,
                )

                panel.assign_syntax(
                    "Packages/Regular Expressions/RegExp.sublime-syntax"
                )
            else:
                self.send_request(client, pattern)
        else:
            self.window.status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )


class TutkainDirCommand(TextCommand):
    def send_request(self, client, symbol):
        client.send_op(
            {"op": edn.Keyword("dir"), "ns": namespace.name(self.view), "sym": symbol},
            lambda response: query.handle_response(
                self.view.window(), completions.KINDS, response
            ),
        )

    def choose(self, client, results, index):
        if index != -1 and (item := results[index]):
            self.send_request(client, item[edn.Keyword("name")])

    def show_namespaces(self, client, response):
        results = response.get(edn.Keyword("results"), [])
        items = query.to_quick_panel_items(completions.KINDS, results)

        self.view.window().show_quick_panel(
            items, lambda index: self.choose(client, results, index)
        )

    def run(self, _):
        window = self.view.window()
        dialect = dialects.for_view(self.view) or edn.Keyword("clj")

        if client := state.get_client(window, dialect):
            if sel := self.view.sel():
                point = sel[0].begin()

                if self.view.match_selector(point, "meta.symbol") and (
                    symbol := selectors.expand_by_selector(
                        self.view, point, "meta.symbol"
                    )
                ):
                    self.send_request(client, self.view.substr(symbol))
                else:
                    client.send_op(
                        {
                            "op": edn.Keyword("all-namespaces"),
                            "ns": namespace.name(self.view),
                            "dialect": dialect,
                        },
                        lambda response: self.show_namespaces(client, response),
                    )

        else:
            self.view.window().status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )


class TutkainLoadedLibsCommand(TextCommand):
    def run(self, _):
        window = self.view.window()
        dialect = dialects.for_view(self.view) or edn.Keyword("clj")

        if client := state.get_client(window, dialect):
            client.send_op(
                {"op": edn.Keyword("loaded-libs"), "dialect": dialect},
                lambda response: query.handle_response(
                    window, completions.KINDS, response
                ),
            )
        else:
            self.view.window().status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )


class TutkainNewScratchViewInNamespaceCommand(TextCommand):
    def run(self, _):
        view = self.view
        window = view.window()
        dialect = dialects.for_view(view)
        extension = dialects.extension(dialect)

        if file_name := view.file_name():
            name = os.path.splitext(file_name)[0] + ".repl"
        else:
            name = "untitled.repl"

        ns = namespace.name_or_default(view, dialect)

        def writef(file):
            return file.write(f"(in-ns '{ns})\n\n")

        temp.open_file(window, name, extension, writef)


class TutkainExploreStackTraceCommand(TextCommand):
    def goto(self, elements, index):
        if index == -1 and (window := self.view.window()):
            window.focus_view(self.view)
        else:
            location = info.parse_location(elements[index])
            info.goto(
                self.view.window(),
                location,
                flags=sublime.ENCODED_POSITION | sublime.TRANSIENT,
            )

    def handler(self, response):
        if elements := response.get(edn.Keyword("stacktrace")):
            items = []

            for element in elements:
                native = element.get(edn.Keyword("native?"))

                if native:
                    continue

                trigger = element.get(edn.Keyword("name"))
                filename = element.get(edn.Keyword("file-name"))
                line = element.get(edn.Keyword("line"))
                items.append(
                    sublime.QuickPanelItem(
                        trigger,
                        annotation=f"{filename}:{line}",
                        kind=sublime.KIND_FUNCTION,
                    )
                )

            self.view.window().show_quick_panel(
                items,
                lambda index: self.goto(elements, index),
                on_highlight=lambda index: self.goto(elements, index),
            )

    def run(self, _):
        if client := state.get_client(self.view.window(), edn.Keyword("clj")):
            client.send_op({"op": edn.Keyword("resolve-stacktrace")}, self.handler)


class TutkainPromptCommand(WindowCommand):
    def on_done(self, client, code):
        if code:
            client.evaluate_rpc(code, options={"file": "NO_SOURCE_FILE"})
            history.update(self.window, code)

        self.prompt(client)

    def on_change(self, _):
        None

    def prompt(self, client):
        view = self.window.show_input_panel(
            "Input: ",
            history.get(self.window),
            lambda code: self.on_done(client, code),
            self.on_change,
            lambda: None,
        )

        view.settings().set("tutkain_repl_input_panel", True)

    def run(self):
        if client := state.get_client(self.window, edn.Keyword("clj")):
            self.prompt(client)
        else:
            self.window.status_message("⚠ Not connected to a REPL.")


class TutkainToggleAutoSwitchNamespaceCommand(TextCommand):
    def run(self, _):
        s = settings.load()
        current = s.get("auto_switch_namespace")
        s.set("auto_switch_namespace", not current)

        if s.get("auto_switch_namespace"):
            self.view.window().status_message(
                "[⏽] [Tutkain] Automatic namespace switching enabled."
            )
        else:
            self.view.window().status_message(
                "[⭘] [Tutkain] Automatic namespace switching disabled."
            )


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


class TutkainRefreshClojuredocsCacheCommand(WindowCommand):
    def run(self):
        sublime.set_timeout_async(lambda: clojuredocs.refresh_cache(self.window), 0)


class TutkainShowClojuredocsExamplesCommand(TextCommand):
    def run(self, _):
        clojuredocs.show_examples(self.view)


class TutkainZapCommasCommand(TextCommand):
    def find_commas(self):
        return reversed(self.view.find_by_selector("comment.punctuation.comma"))

    def run(self, edit):
        if len(self.view.sel()) == 1 and self.view.sel()[0].empty():
            for comma in self.find_commas():
                self.view.erase(edit, comma)
        else:
            for sel in self.view.sel():
                for comma in filter(
                    lambda comma: sel.contains(comma), self.find_commas()
                ):
                    self.view.erase(edit, comma)


class TutkainMarkFormCommand(TextCommand):
    def run(self, _, scope="outermost"):
        for region in self.view.sel():
            if eval_region := get_eval_region(
                self.view, region, scope, ignore={"comment"}
            ):
                point = eval_region.begin()
                code = self.view.substr(eval_region)
                line, column = self.view.rowcol(point)
                dialect = dialects.for_view(self.view)

                options = {
                    "ns": namespace.name_or_default(self.view, dialect),
                    "region": eval_region.to_tuple(),
                    "line": line,
                    "column": column,
                    "file": self.view.file_name(),
                }

                self.view.window().settings().set(
                    "tutkain_mark",
                    {"code": code, "options": options},
                )

                self.view.window().status_message("Form marked")


class TutkainRemoveNamespaceMappingCommand(TextCommand):
    def unmap(self, client, dialect, results, index):
        if index != -1:
            item = results[index]

            client.send_op(
                {
                    "op": edn.Keyword("remove-namespace-mapping"),
                    "ns": edn.Symbol(item[edn.Keyword("ns")]),
                    "sym": item[edn.Keyword("name")],
                    "dialect": dialect,
                },
                lambda response: self.view.window().status_message(
                    f"""Namespace mapping {response.get(edn.Keyword('ns'))}/{response.get(edn.Keyword('sym'))} removed."""
                ),
            )

    def handler(self, client, dialect, response):
        results = response.get(edn.Keyword("results"), [])
        items = query.to_quick_panel_items(completions.KINDS, results)

        self.view.window().show_quick_panel(
            items, lambda index: self.unmap(client, dialect, results, index)
        )

    def run(self, _):
        window = self.view.window()
        dialect = dialects.for_view(self.view) or edn.Keyword("clj")

        if client := state.get_client(window, dialect):
            client.send_op(
                {
                    "op": edn.Keyword("intern-mappings"),
                    "ns": edn.Symbol(namespace.name_or_default(self.view, dialect)),
                    "dialect": dialect,
                },
                lambda response: self.handler(client, dialect, response),
            )
        else:
            self.view.window().status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )


class TutkainRemoveNamespaceAliasCommand(TextCommand):
    def unmap(self, client, dialect, ns, results, index):
        if index != -1:
            item = results[index]

            client.send_op(
                {
                    "op": edn.Keyword("remove-namespace-alias"),
                    "ns": ns,
                    "sym": item[edn.Keyword("name")],
                    "dialect": dialect,
                },
                lambda response: self.view.window().status_message(
                    f"""Namespace alias {response.get(edn.Keyword('sym'))} removed."""
                ),
            )

    def handler(self, client, dialect, ns, response):
        results = response.get(edn.Keyword("results"), [])
        items = query.to_quick_panel_items(completions.KINDS, results)

        self.view.window().show_quick_panel(
            items, lambda index: self.unmap(client, dialect, ns, results, index)
        )

    def run(self, _):
        window = self.view.window()
        dialect = dialects.for_view(self.view)

        if client := state.get_client(window, dialect):
            ns = edn.Symbol(namespace.name_or_default(self.view, dialect))

            client.send_op(
                {
                    "op": edn.Keyword("alias-mappings"),
                    "ns": ns,
                    "dialect": dialect,
                },
                lambda response: self.handler(client, dialect, ns, response),
            )
        else:
            self.view.window().status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )


class TutkainRemoveNamespaceCommand(TextCommand):
    def remove(self, client, dialect, results, index):
        if index != -1 and (item := results[index]):
            client.send_op(
                {
                    "op": edn.Keyword("remove-namespace"),
                    "ns": item[edn.Keyword("name")],
                    "dialect": dialect,
                },
                lambda response: self.view.window().status_message(
                    f"""Namespace {response.get(edn.Keyword('ns'))} removed."""
                ),
            )

    def handler(self, client, dialect, response):
        results = response.get(edn.Keyword("results"), [])
        items = query.to_quick_panel_items(completions.KINDS, results)

        self.view.window().show_quick_panel(
            items, lambda index: self.remove(client, dialect, results, index)
        )

    def run(self, _):
        window = self.view.window()
        dialect = dialects.for_view(self.view) or edn.Keyword("clj")

        if client := state.get_client(window, dialect):
            client.send_op(
                {
                    "op": edn.Keyword("all-namespaces"),
                    "ns": namespace.name(self.view),
                    "dialect": dialect,
                },
                lambda response: self.handler(client, dialect, response),
            )
        else:
            self.view.window().status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )


class TutkainHardWrapCommand(TextCommand):
    def run(self, edit, width=None):
        if width is None and (rulers := self.view.settings().get("rulers")):
            width = rulers[0]
        elif width is None:
            width = 80

        indent.hard_wrap(self.view, edit, width)


class TutkainSynchronizeDependenciesCommand(WindowCommand):
    def handler(self, response):
        progress.stop()

        if response.get(edn.Keyword("tag")) == edn.Keyword("err"):
            self.window.status_message("⚠ " + response.get(edn.Keyword("val")))
        else:
            self.window.status_message("✓ Synchronizing deps... done.")

    def run(self):
        dialect = edn.Keyword("clj")

        if client := state.get_client(self.window, dialect):
            if "deps.clj" in client.capabilities:
                progress.start("Synchronizing deps...")

                client.send_op(
                    {"op": edn.Keyword("sync-deps")},
                    # TODO: Add aliases support
                    lambda response: self.handler(response),
                )
            else:
                self.window.status_message(
                    "⚠ Tutkain: Synchronize Dependencies requires Clojure v1.12.0-alpha2 or newer."
                )
        else:
            self.window.status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )


class LibQueryInputHandler(TextInputHandler):
    def placeholder(self):
        return "Search libs"

    def validate(self, text):
        return len(text) > 0


repos = {
    "clojars": "Clojars",
    "maven": "Maven Central",
    "github": "GitHub",
}


class RepoInputHandler(ListInputHandler):
    def placeholder(self):
        return "Choose repository"

    def list_items(self):
        return [
            sublime.ListInputItem(
                "Clojars",
                "clojars",
                details="Clojars is an easy to use community repository for open source Clojure libraries.",
            ),
            sublime.ListInputItem(
                "Maven Central",
                "maven",
                details="Discover Java packages, and publish your own.",
            ),
            sublime.ListInputItem(
                "GitHub",
                "github",
                details="An internet hosting service for software development and version control using Git.",
            ),
        ]

    def next_input(self, args):
        if args.get("repo") == "github":
            return None

        return LibQueryInputHandler()


class TutkainAddLibCommand(WindowCommand):
    def input(self, args):
        return RepoInputHandler()

    def add_handler(self, group_id, artifact_id, version, response):
        progress.stop()

        if response.get(edn.Keyword("tag")) == edn.Keyword("err"):
            self.window.status_message("⚠ " + response.get(edn.Keyword("val")))
        else:
            self.window.status_message(
                f"✓ {group_id}/{artifact_id} {version} and its deps added into the runtime."
            )

    def choose_handler(self, client, result):
        group_id = result.get(edn.Keyword("group-id"))
        artifact_id = result.get(edn.Keyword("artifact-id"))
        lib = edn.Symbol(artifact_id, group_id)
        version = result.get(edn.Keyword("version"))

        coords = {lib: version}

        progress.start(f"Adding {group_id}/{artifact_id} {version}...")

        client.send_op(
            {"op": edn.Keyword("add-libs"), "lib-coords": coords},
            lambda response: self.add_handler(group_id, artifact_id, version, response),
        )

    def find_handler(self, client, lib_query, response):
        progress.stop()

        if response.get(edn.Keyword("tag")) == edn.Keyword("err"):
            self.window.status_message("⚠ " + response.get(edn.Keyword("val")))
        else:
            results = response.get(edn.Keyword("results"), [])

            if not results:
                self.window.status_message(f"No results for {lib_query}.")
            else:
                items = []

                for result in results:
                    group_id = result.get(edn.Keyword("group-id"))
                    artifact_id = result.get(edn.Keyword("artifact-id"))
                    version = result.get(edn.Keyword("version"))
                    mvn_version = version.get(edn.Keyword("version", "mvn"))
                    git_tag = version.get(edn.Keyword("tag", "git"))
                    version = mvn_version or git_tag
                    description = result.get(edn.Keyword("description"))

                    if description:
                        description = textwrap.shorten(
                            description, width=100, placeholder="…"
                        )

                    items.append(
                        sublime.QuickPanelItem(
                            f"{group_id}/{artifact_id}",
                            annotation="v" + version,
                            details=description or "",
                        )
                    )

                if items:
                    self.window.show_quick_panel(
                        items,
                        lambda index: None
                        if index == -1
                        else self.choose_handler(client, results[index]),
                        placeholder="Choose lib",
                    )

    def run(self, repo, lib_query=None):
        dialect = edn.Keyword("clj")

        if client := state.get_client(self.window, dialect):
            if "deps.clj" in client.capabilities:
                if lib_query is not None:
                    progress.start(f"""Searching {repos[repo]} for "{lib_query}"...""")

                client.send_op(
                    {
                        "op": edn.Keyword("find-libs"),
                        "repo": edn.Symbol(repo),
                        "q": lib_query,
                    },
                    lambda response: self.find_handler(client, lib_query, response),
                )
            else:
                self.window.status_message(
                    "⚠ Tutkain: Add Lib requires Clojure v1.12.0-alpha2 or newer."
                )
        else:
            self.window.status_message(
                f"⚠ Not connected to a {dialects.name(dialect)} REPL."
            )
