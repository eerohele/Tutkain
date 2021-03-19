panel_name = "tutkain.tap_panel"


def create_panel(window):
    panel = window.find_output_panel(panel_name)

    if panel is None:
        panel = window.create_output_panel(panel_name)
        panel.settings().set("line_numbers", False)
        panel.settings().set("gutter", False)
        panel.settings().set("is_widget", True)
        panel.settings().set("scroll_past_end", False)
        panel.assign_syntax("Clojure (Tutkain).sublime-syntax")

    return panel
