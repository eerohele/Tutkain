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
    active_client=defaultdict(dict)
)


def get_connections():
    return __state["connections"]


def forget_connection(connection: Connection) -> None:
    if connections := get_connections():
        connections.pop(connection.client.id)

        if get_client(connection.dialect) == connection.client:
            __state["active_client"].pop(connection.dialect)

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
    __state["active_client"][connection.dialect] = connection.client


def get_client(dialect: Dialect) -> Union[repl.Client, None]:
    return __state["active_client"].get(dialect)


def get_client_by_id(id: str) -> Union[repl.Client, None]:
    if connection := __state["connections"].get(id):
        return connection.client


def set_active_client(view: View) -> Union[repl.Client, None]:
    client_id = view.settings().get("tutkain_repl_client_id")
    dialect = edn.Keyword(view.settings().get("tutkain_repl_view_dialect"))

    if client := get_client_by_id(client_id):
        __state["active_client"][dialect] = client


def get_active_client_view(dialect: Dialect) -> View:
    client = __state["active_client"][dialect]
    return __state["connections"][client.id].view
