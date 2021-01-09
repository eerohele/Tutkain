def create(window, client):
    view_count = len(window.views_in_group(1))
    suffix = "" if view_count == 0 else f" ({view_count})"

    view = window.new_file()
    view.set_name(f"REPL | {client.host}:{client.port}{suffix}")
    view.settings().set("line_numbers", False)
    view.settings().set("gutter", False)
    view.settings().set("is_widget", True)
    view.settings().set("scroll_past_end", False)
    view.settings().set("tutkain_repl_output_view", True)
    view.set_read_only(True)
    view.set_scratch(True)

    view.assign_syntax("Clojure (Tutkain).sublime-syntax")

    # Move the output view into the second row.
    window.set_view_index(view, 1, view_count)

    return view
