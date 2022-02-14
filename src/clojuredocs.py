import json
import os
import pathlib
import sublime
import urllib
import tempfile

from ..api import edn
from . import dialects
from . import namespace
from . import selectors
from . import settings
from . import state


EXAMPLE_SOURCE_PATH = os.path.join(sublime.cache_path(), "Tutkain", "clojuredocs.edn")
EXAMPLE_URI = "https://clojuredocs.org/clojuredocs-export.json"


def see_also_symbol(see_also):
    to_var = see_also.get("to-var")
    name = to_var.get("name")
    ns = to_var.get("ns")
    return edn.Symbol(name, ns)


def refresh_cache(window, callback=lambda: None):
    window.status_message(f"Downloading from {EXAMPLE_URI}...")

    try:
        response = urllib.request.urlopen(EXAMPLE_URI)
        encoding = response.info().get_content_charset("utf-8")
        data = json.loads(response.read().decode(encoding))

        with open(EXAMPLE_SOURCE_PATH, "w") as file:
            output = {}

            for var in data.get("vars"):
                symbol = edn.Symbol(var.get("name"), var.get("ns"))
                output[symbol] = {}

                if examples := var.get("examples"):
                    output[symbol][edn.Keyword("examples")] = list(map(lambda example: example.get("body"), examples))

                if see_alsos := var.get("see-alsos"):
                    output[symbol][edn.Keyword("see-alsos")] = list(map(see_also_symbol, see_alsos))

            edn.write1(file, output)

        window.status_message("Finished downloading ClojureDocs data.")
        callback()
    except urllib.error.URLError as error:
        sublime.error_message(f"[Tutkain] Error trying to fetch ClojureDocs examples from {EXAMPLE_URI}:\n\n {repr(error)}\n\nAre you connected to the internet?")
    except OSError as error:
        sublime.error_message(f"[Tutkain] Error trying to save ClojureDocs examples into {EXAMPLE_SOURCE_PATH}:\n {repr(error)}")


def send_message(window, client, ns, sym):
    client.backchannel.send({
        "op": edn.Keyword("examples"),
        "source-path": EXAMPLE_SOURCE_PATH,
        "ns": ns,
        "sym": sym
    }, lambda response: handler(window, client, response))


def handler(window, client, response):
    symbol = response.get(edn.Keyword("symbol"))
    examples = response.get(edn.Keyword("examples"))
    see_alsos = response.get(edn.Keyword("see-alsos"))

    if examples or see_alsos:
        descriptor, temp_path = tempfile.mkstemp(".clj")

        try:
            path = pathlib.Path(temp_path)

            with open(path, "w") as file:
                if examples:
                    file.write(f";; ClojureDocs examples for {symbol}")

                    for example in examples:
                        file.write("\n\n"+ example)

                if see_alsos:
                    if examples:
                        file.write("\n\n")

                    file.write(":see-also [")
                    file.write(", ".join(map(lambda see_also: str(see_also), see_alsos)))
                    file.write("]")

            view = window.open_file(f"{path}", flags=sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT)

            view.settings().set("tutkain_temp_file", {
                "path": temp_path,
                "descriptor": descriptor,
                "name": f"{symbol.name}.clj"
            })

            view.set_scratch(True)

            # Switch to the symbol's namespace
            if (ns := symbol.namespace) and settings.load().get("auto_switch_namespace"):
                client.switch_namespace(ns)
        except:
            if os.path.exists(temp_path):
                os.close(descriptor)
                os.remove(temp_path)
    else:
        window.status_message(f"No examples found for {symbol}.")


def show(view):
    window = view.window()

    if client := state.get_client(window, edn.Keyword("clj")):
        point = view.sel()[0].begin()

        if dialects.for_point(view, point) != edn.Keyword("clj"):
            view.window().status_message("ERR: ClojureDocs examples are only available for Clojure.")
        else:
            ns = edn.Symbol(namespace.name(view) or namespace.default(edn.Keyword("clj")))

            if region := selectors.expand_by_selector(view, point, "meta.symbol"):
                sym = edn.Symbol(view.substr(region))
                send_message(window, client, ns, sym)
            else:
                input_panel = view.window().show_input_panel(
                    "Symbol: ",
                    "",
                    lambda sym: send_message(window, client, ns, edn.Symbol(sym)),
                    lambda _: None,
                    lambda: None
                )

                input_panel.assign_syntax("Packages/Tutkain/Clojure (Tutkain).sublime-syntax")
                input_panel.settings().set("auto_complete", True)
    else:
        view.window().status_message("ERR: Not connected to a Clojure REPL.")


def show_examples(view):
    if not os.path.exists(EXAMPLE_SOURCE_PATH):
        sublime.set_timeout_async(
            lambda: refresh_cache(view.window(), lambda: show(view)),
            0
        )
    else:
        show(view)
