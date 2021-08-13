import binascii


def encode(string):
    """Given a string, return a Base64-encoded version of that string, without
    newlines."""
    return binascii.b2a_base64(string.encode("utf-8"), newline=False).decode("utf-8").rstrip()
