from collections import defaultdict
from sublime import View, active_window
from typing import Union, TypedDict
from dataclasses import dataclass
from . import repl
from . import dialects
from ..api import edn


WindowId = int
ViewId = int
Dialect = edn.Keyword


class State(TypedDict):
    pass


@dataclass(eq=True, frozen=True)
class Connection:
    client: repl.Client
    dialect: Dialect
    view: View


__state = State(
    connections=defaultdict(dict),
    active_connection=defaultdict(dict)
)


def get_connections():
    return __state["connections"]


def forget_connection(connection: Connection) -> None:
    if connections := get_connections():
        connections.pop(connection.client.id)

        if get_client(connection.dialect) == connection.client:
            __state["active_connection"].pop(connection.dialect)

            # If there's only one remaining connection with the same dialect as
            # the one we're currently disconnecting, set that as the active client.
            alts = list(filter(lambda this: this.dialect == connection.dialect, connections.values()))

            if len(alts) == 1:
                __state["active_connection"][connection.dialect] = alts[0]

        window = connection.view.window() or active_window()

        # Destroy output panel if this is the only remaining connection that
        # uses the panel.
        if not list(filter(lambda this: this.view.element() == "output:output", connections)):
            # TODO: Never destroy the panel, just clear it instead?
            window.destroy_output_panel(repl.views.output_panel_name())

        # Clear test markers if this is the only remaining connection for
        # this dialect.
        if not list(filter(lambda this: this.dialect == connection.dialect, connections)):
            if view := window.active_view():
                if dialects.for_view(view) == connection.dialect:
                    view.run_command("tutkain_clear_test_markers")


def register_connection(view: View, dialect: Dialect, client: repl.Client) -> None:
    connection = Connection(client, dialect, view)
    connection.client.on_close = lambda: forget_connection(connection)

    __state["connections"][connection.client.id] = connection
    __state["active_connection"][connection.dialect] = connection


def get_client(dialect: Dialect) -> Union[repl.Client, None]:
    if connection := __state["active_connection"].get(dialect):
        return connection.client


def set_active_connection(client_id: str) -> Union[repl.Client, None]:
    if connection := __state["connections"].get(client_id):
        __state["active_connection"][connection.dialect] = connection


def get_active_connection_view(dialect: Dialect) -> View:
    connection = __state["active_connection"][dialect]
    return __state["connections"][connection.client.id].view
