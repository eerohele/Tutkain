def format(message):
    if "value" in message:
        return message["value"].replace("\r", "")
    if "summary" in message:
        return message["summary"] + "\n"
    if "tap" in message:
        return message["tap"]
    if "nrepl.middleware.caught/throwable" in message:
        return message["nrepl.middleware.caught/throwable"]
    if "out" in message:
        return message["out"]
    if "in" in message:
        ns = message.get("ns") or ""
        return "{}=> {}\n".format(ns, message["in"])
    if "err" in message:
        return message.get("err")
    if "versions" in message:
        result = []

        versions = message.get("versions")

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
