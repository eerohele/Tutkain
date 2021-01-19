from .. import state


def create(window, host, port):
    target_group = window.num_groups() - 1
    view_count = len(window.views_in_group(target_group))
    suffix = "" if view_count == 0 else f" ({view_count})"

    view = window.new_file()
    view.set_name(f"REPL | {host}:{port}{suffix}")
    view.settings().set("line_numbers", False)
    view.settings().set("gutter", False)
    view.settings().set("is_widget", True)
    view.settings().set("scroll_past_end", False)
    view.settings().set("show_definitions", False)
    view.settings().set("tutkain_repl_output_view", True)
    view.settings().set("tutkain_repl_host", host)
    view.settings().set("tutkain_repl_port", port)
    view.set_read_only(True)
    view.set_scratch(True)

    view.assign_syntax("Clojure (Tutkain).sublime-syntax")

    window.set_view_index(view, target_group, view_count)

    return view


def configure(window, repl, view_id=None):
    view = view_id and next(
        filter(lambda view: view.id() == view_id, window.views()),
        None,
    ) or create(window, repl.client.host, repl.client.port)

    state.set_view_client(view, repl.client)
    state.set_active_repl_view(view)

    return view


def is_output_view(view):
    return view.settings().get("tutkain_repl_output_view")
