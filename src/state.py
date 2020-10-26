import collections


state = {
    "active_repl_view": collections.defaultdict(dict),
    "client_by_view": collections.defaultdict(dict),
    "view_by_session": collections.defaultdict(dict)
}


def set_view_client(view, client):
    state["client_by_view"][view.id()] = client


def get_active_repl_view(window):
    return state.get("active_repl_view").get(window.id())


def set_active_repl_view(view):
    state["active_repl_view"][view.window().id()] = view


def get_view_client(view):
    return view and state["client_by_view"].get(view.id())


def get_active_view_client(window):
    return get_view_client(get_active_repl_view(window))


def get_active_view_sessions(window):
    client = get_active_view_client(window)
    return client and client.sessions_by_owner


def get_session_by_owner(window, owner):
    sessions = get_active_view_sessions(window)
    return sessions and sessions.get(owner)


def forget_repl_view(view):
    if view and view.id() in state["client_by_view"]:
        del state["client_by_view"][view.id()]
