from collections import defaultdict
from sublime import View, Window
from typing import Union, TypedDict
from dataclasses import dataclass
from . import repl
from . import dialects
from . import namespace
from . import settings
from . import status
from ..api import edn


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
    active_connection=defaultdict(dict)
)


def get_connections():
    return __state["connections"]


def get_connection_by_id(client_id: Union[str, None]) -> Union[Connection, None]:
    get_connections().get(client_id)


def register_connection(view: View, window: Window, client: repl.Client) -> None:
    connection = Connection(client, window, view)

    def forget_connection():
        del __state["connections"][connection.client.id]
        remaining_connections = list(__state["connections"].values())

        if get_active_connection(window, connection.client.dialect) == connection:
            __state["active_connection"][connection.window.id()].pop(connection.client.dialect)

        # Destroy tap panel if this is the only remaining connection for
        # this window.
        if not list(filter(lambda this: this.window.id() == connection.window.id(), remaining_connections)):
            connection.window.destroy_output_panel(repl.views.tap_panel_name(connection.view))

        # Destroy output panel if this is the only remaining connection that
        # uses the panel.
        if not list(filter(lambda this: this.view.element() == "output:output", remaining_connections)):
            # TODO: Never destroy the panel, just clear it instead?
            connection.window.destroy_output_panel(repl.views.output_panel_name())

        # Clear test markers if this is the only remaining connection for
        # this dialect.
        if not list(filter(lambda this: this.dialect == connection.client.dialect, remaining_connections)):
            if view := connection.window.active_view():
                if dialects.for_view(view) == connection.client.dialect:
                    view.run_command("tutkain_clear_test_markers")

        window and status.erase_connection_status(window.active_view())

    connection.client.on_close = forget_connection

    __state["connections"][connection.client.id] = connection
    __state["active_connection"][connection.window.id()][connection.client.dialect] = connection


def get_active_connection(window: Window, dialect: Dialect) -> Union[Connection, None]:
    if window:
        return __state["active_connection"].get(window.id(), {}).get(dialect)


def get_client(window: Window, dialect: Dialect) -> Union[repl.Client, None]:
    if connection := get_active_connection(window, dialect):
        return connection.client


def set_active_connection(window: Window, connection: Union[Connection, None]) -> None:
    if connection:
        __state["active_connection"][window.id()][connection.client.dialect] = connection


def get_active_output_view(window: Window) -> Union[View, None]:
    if panel := window.find_output_panel(repl.views.output_panel_name()):
        return panel

    for group in range(window.num_groups() + 1):
        if (view := window.active_view_in_group(group)) and repl.views.get_dialect(view):
            return view


def focus_active_runtime_view(window: Window, dialect: Dialect) -> None:
    active_view = window.active_view()

    if window and repl.views.get_dialect(get_active_output_view(window)) != dialect:
        # Focus the REPL view for the given dialect
        window.focus_view(get_active_connection(window, dialect).view)
        # Focus the view that was initially active
        window.focus_view(active_view)


def on_activated(window, view):
    if window and window.active_panel() != "input" and (
        dialect := dialects.for_view(view)
    ) and (
        client := get_client(window, dialect)
    ):
        status.set_connection_status(view, client)

        if settings.load().get("auto_switch_namespace", True) and client.has_backchannel() and client.ready:
            ns = namespace.name(view) or namespace.default(dialect)
            client.switch_namespace(ns)
    else:
        status.erase_connection_status(view)
