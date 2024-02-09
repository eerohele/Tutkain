from collections import defaultdict, deque
from dataclasses import dataclass
from typing import TypedDict, Union

from sublime import View, Window

from ..api import edn
from . import dialects, repl, status

WindowId = int
ViewId = int
Dialect = edn.Keyword


class State(TypedDict):
    pass


@dataclass(eq=True, frozen=True)
class Connection:
    client: repl.Client
    window: Window
    view: View


__state = State(
    connections=defaultdict(dict),
    active_connection=defaultdict(dict),
    gutter_markers=defaultdict(dict),
)


def get_connections():
    return __state["connections"]


def has_connections():
    return bool(get_connections())


def get_connection_by_id(client_id: Union[str, None]) -> Union[Connection, None]:
    return get_connections().get(client_id)


MARKER_TAGS = {
    edn.Keyword("ret"),
    edn.Keyword("in"),
    edn.Keyword("err"),
    edn.Keyword("tap"),
}


def reset_gutter_markers(view: View) -> None:
    if view:
        for tag in MARKER_TAGS:
            view.erase_regions(f"tutkain_gutter_marks/{tag.name}")
            __state["gutter_markers"].get(view.id(), {}).get(tag, []).clear()


def get_gutter_markers(view: View):
    if not view:
        return {}
    else:
        return __state["gutter_markers"].get(view.id())


def register_connection(view: View, window: Window, client: repl.Client) -> None:
    connection = Connection(client, window, view)

    for tag in MARKER_TAGS:
        if not __state["gutter_markers"].get(view.id(), {}).get(tag):
            __state["gutter_markers"][view.id()][tag] = deque([], 1000)

    def forget_connection():
        del __state["connections"][connection.client.id]
        remaining_connections = list(__state["connections"].values())

        if get_active_connection(window, connection.client.dialect) == connection:
            __state["active_connection"][connection.window.id()].pop(
                connection.client.dialect
            )

        # Destroy tap panel if this is the only remaining connection for
        # this window.
        if not list(
            filter(
                lambda this: this.window.id() == connection.window.id(),
                remaining_connections,
            )
        ):
            connection.window.destroy_output_panel(
                repl.views.tap_panel_name(connection.view)
            )

        # Destroy output panel if this is the only remaining connection that
        # uses the panel.
        if not list(
            filter(
                lambda this: this.view.element() == "output:output",
                remaining_connections,
            )
        ):
            # TODO: Never destroy the panel, just clear it instead?
            connection.window.destroy_output_panel(repl.views.output_panel_name())

        # Clear test markers if this is the only remaining connection for
        # this dialect.
        if not list(
            filter(
                lambda this: this.dialect == connection.client.dialect,
                remaining_connections,
            )
        ):
            if view := connection.window.active_view():
                if dialects.for_view(view) == connection.client.dialect:
                    view.run_command("tutkain_clear_test_markers")

        window and status.erase_connection_status(window.active_view())

    connection.client.on_close = forget_connection

    __state["connections"][connection.client.id] = connection
    __state["active_connection"][connection.window.id()][
        connection.client.dialect
    ] = connection


def get_active_connection(window: Window, dialect: Dialect) -> Union[Connection, None]:
    if window:
        return __state["active_connection"].get(window.id(), {}).get(dialect)


def get_client(window: Window, dialect: Dialect) -> Union[repl.Client, None]:
    if connection := get_active_connection(window, dialect):
        return connection.client


def set_active_connection(window: Window, connection: Union[Connection, None]) -> None:
    if connection:
        __state["active_connection"][window.id()][
            connection.client.dialect
        ] = connection


def get_active_output_view(window: Window) -> Union[View, None]:
    if panel := window.find_output_panel(repl.views.output_panel_name()):
        return panel

    for group in range(window.num_groups() + 1):
        if (view := window.active_view_in_group(group)) and repl.views.get_dialect(
            view
        ):
            return view


def focus_active_runtime_view(window: Window, dialect: Dialect) -> None:
    active_view = window.active_view()

    if window and repl.views.get_dialect(get_active_output_view(window)) != dialect:
        # Focus the REPL view for the given dialect
        if connection := get_active_connection(window, dialect):
            window.focus_view(connection.view)

        # Focus the view that was initially active
        window.focus_view(active_view)


def on_activated(window, view):
    if (
        window
        and window.active_panel() != "input"
        and (dialect := dialects.for_view(view))
        and (client := get_client(window, dialect))
    ):
        status.set_connection_status(view, client)
    else:
        status.erase_connection_status(view)
