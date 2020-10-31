from ..log import log


def format(response, settings={}):
    if "status" in response and "namespace-not-found" in response["status"]:
        return ":tutkain/namespace-not-found\n"
    if "status" in response and "session-idle" in response["status"]:
        return ":tutkain/nothing-to-interrupt\n"
    if "value" in response:
        return response["value"].replace("\r", "")
    if "summary" in response:
        return response["summary"] + "\n"
    if "tap" in response:
        return response["tap"]
    if "nrepl.middleware.caught/throwable" in response:
        return response["nrepl.middleware.caught/throwable"]
    if "out" in response:
        return response["out"]
    if "in" in response:
        ns = response.get("ns", "")
        return f"""{ns}=> {response["in"]}\n"""
    if "err" in response:
        return response.get("err")
    if "versions" in response:
        result = []

        versions = response.get("versions")

        clojure_version = versions.get("clojure")
        nrepl_version = versions.get("nrepl")
        babashka_version = versions.get("babashka")

        if clojure_version:
            major = clojure_version.get("major")
            minor = clojure_version.get("minor")
            incremental = clojure_version.get("incremental")
            result.append(f"""Clojure {major}.{minor}.{incremental}""")
        elif babashka_version:
            result.append(f"""Babashka {babashka_version}""")
            result.append(f"""babashka.nrepl {versions.get("babashka.nrepl")}""")

        if nrepl_version:
            major = nrepl_version.get("major")
            minor = nrepl_version.get("minor")
            incremental = nrepl_version.get("incremental")
            result.append(f"""nREPL {major}.{minor}.{incremental}""")

        return "\n".join(result) + "\n"
    if "status" in response and "done" in response["status"] and settings.get("newline_on_done"):
        return "\n"


def format_loop(recvq, printq, tapq, settings):
    try:
        log.debug({"event": "thread/start"})

        while True:
            response = recvq.get()

            if response is None:
                break

            log.debug({"event": "formatq/recv", "data": response})

            if "tap" in response:
                tapq.put(response)
            else:
                printable = format(response, settings)

                if printable:
                    printq.put({"printable": printable, "response": response})
    finally:
        printq.put(None)
        tapq.put(None)
        log.debug({"event": "thread/exit"})
