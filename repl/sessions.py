import collections

by_owner = collections.defaultdict(dict)
by_id = collections.defaultdict(dict)


def get_by_id(id):
    return by_id.get(id)


def get_by_owner(window_id, owner):
    by_window = by_owner.get(window_id)

    if by_window:
        return by_window.get(owner)


def register(window_id, owner, session):
    by_id[session.id] = session
    by_owner[window_id][owner] = session


def deregister(window_id):
    sessions = by_owner.get(window_id)

    if sessions:
        for _, session in sessions.items():
            by_id.pop(session.id, None)

    by_owner.pop(window_id, None)


def terminate(window_id):
    for session in [get_by_owner(window_id, 'user'),
                    get_by_owner(window_id, 'plugin')]:
        if session:
            session.terminate()

    deregister(window_id)


def wipe():
    for id, session in by_id.items():
        session.terminate()

    by_owner.clear()
    by_id.clear()
