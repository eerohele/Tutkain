import os
import sublime

from . import base64
from . import forms
from . import namespace
from . import sexp
from .progress import ProgressBar
from ..api import edn


RESULTS_SETTINGS_KEY = "tutkain_clojure_test_results"


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


def results(view):
    """
    Returns test results persisted in settings.
    """
    return view.settings().get(RESULTS_SETTINGS_KEY, [])


def unsuccessful(view):
    """
    Returns unsuccessful test results, fail and error, persisted in settings.
    """

    def result_line(result):
        begin, _ = result["region"]

        return view.rowcol(begin)[0] + 1

    def unsuccessful_type(result):
        return result["type"] == "fail" or result["type"] == "error"

    l = list(filter(unsuccessful_type, results(view)))

    # Results must be sorted by line.
    l.sort(key=result_line)

    return l


def response_results(view, response):
    """
    Returns a dict with "fail", "error" and "pass" keys.

    "fail" and "error" are lists of dict with keys:
      - "name"
      - "type"
      - "region"
      - "expected"
      - "actual"

    "pass" is a list of dict with keys:
      - "name"
      - "type"
      - "region"
    """

    results = {"fail": {}, "error": {}, "pass": {}}

    def var_meta_name(result):
        return result[edn.Keyword("var-meta")][edn.Keyword("name")]

    if edn.Keyword("fail") in response:
        for result in response[edn.Keyword("fail")]:
            line = result[edn.Keyword("line")] - 1
            point = view.text_point(line, 0)

            results["fail"][line] = {
                "name": var_meta_name(result),
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
                "name": var_meta_name(result),
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
                    "name": var_meta_name(result),
                    "type": result[edn.Keyword("type")],
                    "region": sublime.Region(point, point),
                }

    return results


def serializable_results(results):
    """
    Returns a list of results suitable for persistence.

    A result is a dict with keys "name", "type", and "region".

    Where:
        - "name" is the name of the test var;
        - "type" is one of "pass", "fail", or "error"
        - "region" is encoded as a tuple(begin, end).
    """

    def serialize(result):
        return {
            "name": result["name"].name,
            "type": result["type"].name,
            "region": result["region"].to_tuple()
        }

    return [serialize(result)
            for result_type in ["pass", "fail", "error"]
            for result in results[result_type].values()]


def add_markers(view, results):
    view.run_command("tutkain_clear_test_markers")

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
        results = response_results(view, response)

        # Persist results so it's possible to create UIs to present it later.
        view.settings().set(RESULTS_SETTINGS_KEY, serializable_results(results))

        add_markers(view, results)
        client.recvq.put(response)
        progress.stop()

    code = view.substr(sublime.Region(0, view.size()))

    client.backchannel.send({
        "op": edn.Keyword("test"),
        "ns": namespace.name(view),
        "code": base64.encode(code.encode("utf-8")),
        "file": view.file_name(),
        "vars": test_vars
    }, handler=handler)


def run(view, client, test_vars=[]):
    if client is None:
        view.window().status_message("ERR: Not connected to a REPL.")
    else:
        progress.start()
        run_tests(view, client, test_vars)
