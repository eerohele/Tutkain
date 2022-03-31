import os
import pathlib
import tempfile
import sublime


def open_file(window, file_name, extension=".clj", writef=None):
    descriptor, temp_path = tempfile.mkstemp(extension)

    try:
        path = pathlib.Path(temp_path)

        if writef:
            with open(path, "w") as file:
                writef(file)

        view = window.open_file(f"{path}", flags=sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT)

        view.settings().set("tutkain_temp_file", {
            "path": temp_path,
            "descriptor": descriptor,
            "name": file_name,
            "selection": "end"
        })

        view.set_scratch(True)
    except:
        if os.path.exists(temp_path):
            os.close(descriptor)
            os.remove(temp_path)
