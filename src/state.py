from collections import defaultdict
from sublime import View, Window
from typing import Union, TypedDict
from dataclasses import dataclass
from . import repl
from . import dialects
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
        connections = __state["connections"]

        window.destroy_output_panel("tutkain.history_preview_panel")

        if get_client(connection.window, connection.client.dialect) == connection.client:
            __state["active_connection"].pop(connection.client.dialect)

            # If there's only one remaining connection with the same dialect as
            # the one we're currently disconnecting, set that as the active client.
            alts = list(filter(lambda this: this.dialect == connection.client.dialect, connections.values()))

            if len(alts) == 1:
                __state["active_connection"][connection.client.dialect] = alts[0]

        # Destroy tap panel if this is the only remaining connection for
        # this window.
        if not list(filter(lambda this: this.window.id() == connection.window.id(), connections)):
            connection.window.destroy_output_panel(repl.views.tap_panel_name(connection.view))

        # Destroy output panel if this is the only remaining connection that
        # uses the panel.
        if not list(filter(lambda this: this.view.element() == "output:output", connections)):
            # TODO: Never destroy the panel, just clear it instead?
            connection.window.destroy_output_panel(repl.views.output_panel_name())

        # Clear test markers if this is the only remaining connection for
        # this dialect.
        if not list(filter(lambda this: this.dialect == connection.client.dialect, connections)):
            if view := connection.window.active_view():
                if dialects.for_view(view) == connection.client.dialect:
                    view.run_command("tutkain_clear_test_markers")

        window and status.erase_connection_status(window.active_view())

    connection.client.on_close = forget_connection

    __state["connections"][connection.client.id] = connection
    __state["active_connection"][connection.client.dialect] = connection


def get_client(window: Window, dialect: Dialect) -> Union[repl.Client, None]:
    if window and (connection := __state["active_connection"].get(dialect)):
        return connection.client


def set_active_connection(client_id: str) -> Union[repl.Client, None]:
    if connection := __state["connections"].get(client_id):
        __state["active_connection"][connection.client.dialect] = connection


def get_active_connection_view(dialect: Dialect) -> View:
    connection = __state["active_connection"][dialect]
    return __state["connections"][connection.client.id].view
