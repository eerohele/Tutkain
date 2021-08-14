import os
import sublime

from . import base64
from . import forms
from . import namespace
from . import sexp
from .progress import ProgressBar
from ..api import edn


progress = ProgressBar("[Tutkain] Running tests...")


def current(view, point):
    for s in sexp.walk_outward(view, point, edge=True):
        head = forms.find_next(view, s.open.end())

        if view.match_selector(head.begin(), "meta.deftest.clojure"):
            form = forms.seek_forward(
                view,
                head.end(),
                lambda form: view.match_selector(form.begin(), "meta.test-var.clojure"),
            )

            if form:
                return view.substr(form)


def add_annotation(response):
    args = {
        "reference": response["expected"],
        "actual": response["actual"]
    }

    return """
    <a style="font-size: 0.8rem"
       href='{}'>{}</a>
    """.format(
        sublime.command_url("tutkain_open_diff_window", args=args),
        "diff" if response.get("type", edn.Keyword("fail")) == edn.Keyword("fail") else "show",
    )


def region_key(view, result_type):
    return "{}:{}".format(view.file_name(), result_type)


def regions(view, result_type):
    return view.get_regions(region_key(view, result_type))


def add_markers(view, response):
    view.run_command("tutkain_clear_test_markers")

    results = {"fail": {}, "error": {}, "pass": {}}

    if edn.Keyword("fail") in response:
        for result in response[edn.Keyword("fail")]:
            line = result[edn.Keyword("line")] - 1
            point = view.text_point(line, 0)

            results["fail"][line] = {
                "type": result[edn.Keyword("type")],
                "region": sublime.Region(point, point),
                "expected": result[edn.Keyword("expected")],
                "actual": result[edn.Keyword("actual")],
            }

    if edn.Keyword("error") in response:
        for result in response[edn.Keyword("error")]:
            line = result[edn.Keyword("var-meta")][edn.Keyword("line")] - 1
            column = result[edn.Keyword("var-meta")][edn.Keyword("column")] - 1
            point = view.text_point(line, column)

            results["error"][line] = {
                "type": result[edn.Keyword("type")],
                "region": forms.find_next(view, point),
                "expected": result[edn.Keyword("expected")],
                "actual": result[edn.Keyword("actual")],
            }

    if edn.Keyword("pass") in response:
        for result in response[edn.Keyword("pass")]:
            line = result[edn.Keyword("line")] - 1
            point = view.text_point(line, 0)

            # Only add pass for line if there's no fail for the same line.
            if line not in results["fail"]:
                results["pass"][line] = {
                    "type": result[edn.Keyword("type")],
                    "region": sublime.Region(point, point),
                }

    passes = results["pass"].values()
    if passes:
        view.add_regions(
            region_key(view, "passes"),
            [p["region"] for p in passes],
            scope="region.greenish",
            icon="circle",
        )

    failures = results["fail"].values()
    if failures:
        view.add_regions(
            region_key(view, "failures"),
            [f["region"] for f in failures],
            scope="region.redish",
            icon="circle",
            annotations=[add_annotation(f) for f in failures],
        )

    errors = results["error"].values()
    if errors:
        view.add_regions(
            region_key(view, "errors"),
            [e["region"] for e in errors],
            scope="region.orangish",
            icon="circle",
            annotation_color="orange",
            annotations=[add_annotation(e) for e in errors],
            flags=sublime.DRAW_NO_FILL,
        )


def run_tests(view, client, test_vars):
    def handler(response):
        add_markers(view, response)
        client.recvq.put(response)
        progress.stop()

    code = view.substr(sublime.Region(0, view.size()))

    client.backchannel.send({
        "op": edn.Keyword("test"),
        "ns": namespace.name(view),
        "code": base64.encode(code),
        "file": view.file_name(),
        "vars": test_vars
    }, handler=handler)


def run(view, client, test_vars=[]):
    if client is None:
        view.window().status_message("ERR: Not connected to a REPL.")
    else:
        progress.start()
        run_tests(view, client, test_vars)
