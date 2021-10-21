from collections import defaultdict
from sublime import View

from . import repl
from ..api import edn


WindowId = int
ViewId = int
Dialect = edn.Keyword


__state = defaultdict(dict)


def register_client(client: repl.Client) -> None:
    __state["client_by_id"][client.id] = client


def get_client(dialect: Dialect):
    return __state.get("active_client", {}).get(dialect)


def view_client(view: View):
    return __state.get("client_by_id", {}).get(view.settings().get("tutkain_repl_client_id"))


def set_active_client(dialect: Dialect, client: repl.Client) -> None:
    if dialect and client:
        __state["active_client"][dialect] = client


def set_active_repl_view(dialect: Dialect, view: View) -> None:
    if dialect and view:
        __state["active_repl_view"][dialect] = view


def active_repl_view(dialect: Dialect) -> View:
    return __state.get("active_repl_view", {}).get(dialect)


def forget_client(dialect: Dialect, client: repl.Client) -> None:
    if client:
        if active_client := get_client(dialect):
            if active_client == client:
                del __state["active_client"][dialect]

        if client.id in __state.get("client_by_id"):
            del __state["client_by_id"][client.id]


def forget_active_repl_view(dialect: Dialect, view: View) -> None:
    if view == active_repl_view(dialect):
        del __state["active_repl_view"][dialect]


def get_state():
    return __state
