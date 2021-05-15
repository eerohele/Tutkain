from collections import defaultdict
from sublime import View, Window
from typing import Dict, TypedDict, Union

from .repl.client import Client
from ..api import edn


WindowId = int
ViewId = int
Dialect = edn.Keyword


class State(TypedDict):
    active_repl_view: Dict[WindowId, View]
    client_by_view: Dict[ViewId, Dict[Dialect, Client]]


__state = State(active_repl_view=defaultdict(dict), client_by_view=defaultdict(dict))


def set_view_client(view: View, dialect: Dialect, client: Client) -> None:
    __state["client_by_view"][view.id()][dialect] = client


def repl_view(window: Window) -> Union[View, None]:
    if window:
        return __state.get("active_repl_view").get(window.id())


def set_repl_view(view: View) -> None:
    __state["active_repl_view"][view.window().id()] = view


def view_client(view: View, dialect: Dialect) -> Union[Client, None]:
    if view:
        return __state["client_by_view"].get(view.id(), {}).get(dialect)


def client(window: Window, dialect: Dialect) -> Union[Client, None]:
    """Return the Client for the REPL view that is active in the given Window."""
    if view := repl_view(window):
        return view_client(view, dialect)


def forget_repl_view(view: View) -> None:
    if view and view.id() in __state["client_by_view"]:
        del __state["client_by_view"][view.id()]
