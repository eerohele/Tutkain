import binascii


def encode(bs):
    """Given a bytes object, return a Base64-encoded version of that object, without
    newlines."""
    return binascii.b2a_base64(bs, newline=False).decode("utf-8").rstrip()
