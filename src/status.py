from . import dialects


def set_connection_status(view, client):
    if view and dialects.for_view(view):
        view.set_status(
            "tutkain_connection_status",
            f"🟢 {client.host}:{client.port} ({dialects.name(client.dialect)})",
        )


def erase_connection_status(view):
    if view:
        view.erase_status("tutkain_connection_status")
