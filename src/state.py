from collections import defaultdict
from sublime import View, Window
from typing import Dict, TypedDict, Union

from .repl.client import Client
from ..api import edn


WindowId = int
ViewId = int
Dialect = edn.Keyword


class State(TypedDict):
    active_repl_view: Dict[WindowId, Dict[Dialect, View]]
    client_by_view: Dict[ViewId, Dict[Dialect, Client]]


__state = State(active_repl_view=defaultdict(dict), client_by_view=defaultdict(dict))


def set_view_client(view: View, dialect: Dialect, client: Client) -> None:
    __state["client_by_view"][view.id()][dialect] = client


def repl_view(window: Window, dialect: Dialect) -> Union[View, None]:
    if window:
        return __state.get("active_repl_view").get(window.id(), {}).get(dialect)


def set_repl_view(view: View, dialect: Dialect) -> None:
    if window := view.window():
        __state["active_repl_view"][window.id()][dialect] = view
    else:
        raise ValueError(f"View {view.id()} has no window")


def view_client(view: View, dialect: Dialect) -> Union[Client, None]:
    if view:
        return __state["client_by_view"].get(view.id(), {}).get(dialect)


def client(window: Window, dialect: Dialect) -> Union[Client, None]:
    if view := repl_view(window, dialect):
        return view_client(view, dialect)


def forget_repl_view(view: View, dialect: Dialect) -> None:
    if view and __state["client_by_view"].get(view.id(), {}).get(dialect):
        del __state["client_by_view"][view.id()][dialect]
