import os
import sublime


def load():
    return sublime.load_settings("Tutkain.sublime-settings")


def source_root():
    return os.path.join(
        sublime.packages_path(), "Tutkain", "clojure", "src", "tutkain"
    )
