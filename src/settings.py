import os
import sublime

from ..api import edn


def load():
    return sublime.load_settings("Tutkain.sublime-settings")


def source_root():
    return os.path.join(sublime.packages_path(), "Tutkain", "clojure", "src", "tutkain")


def backchannel_options(dialect, backchannel=True):
    if dialect == edn.Keyword("cljs"):
        return {
            "enabled": backchannel,
            "port": load().get("clojurescript").get("backchannel").get("port"),
            "bind_address": load()
            .get("clojurescript")
            .get("backchannel")
            .get("bind_address", "localhost"),
        }
    elif dialect == edn.Keyword("clj"):
        return {
            "enabled": backchannel,
            "port": load().get("clojure").get("backchannel").get("port"),
            "bind_address": load()
            .get("clojure")
            .get("backchannel")
            .get("bind_address", "localhost"),
        }
    elif dialect == edn.Keyword("bb"):
        return {
            "enabled": backchannel,
            "port": load().get("babashka").get("backchannel").get("port"),
            "bind_address": load()
            .get("babashka")
            .get("backchannel")
            .get("bind_address", "localhost"),
        }
