# -*- coding: utf-8 -*-
"""
Read bencoded bytes from a socket and turn them into Python values or turn
Python values into bencoded bytes.

Example:

    import tutkain.bencode as bencode

    socket = socket.sockets(socket.AF_INET, socket.SOCK_STREAM)
    socket.connect(('localhost', 1234))

    # Wait for someone to put a bencoded value onto the socket.
    #
    # For example, given:
    #
    #     b'd3:bar4:spam3:fooi42ee'

    print(bencode.read(socket))
    # => {'foo': 42, 'bar': 'spam'}

    print(bencode.write({'foo': 42, 'bar': 'spam'}))
    # => b'd3:bar4:spam3:fooi42ee'

Has complete faith in the sending end. That is, does not try to recover from
any errors.
"""

from functools import partial


ENCODING = 'utf-8'


def read_until(socket, terminator):
    """Read bytes from a socket until the given terminator byte.

    Return the bytes, excluding the terminator byte."""
    bs = bytearray()

    for byte in iter(partial(socket.recv, 1), terminator):
        bs.extend(byte)

    return bs


def read_list(socket):
    """Read a bencoded list into a Python list."""
    def aux(socket, acc):
        item = read(socket)

        if item is None:
            return acc
        else:
            acc.append(item)
            return aux(socket, acc)

    return aux(socket, [])


def into_dict(l):
    """Convert a list into a dict."""
    return {l[i]: l[i + 1] for i in range(0, len(l), 2)}


def read_dict(socket):
    """Read a bencoded dictionary into a Python dict."""
    return into_dict(read_list(socket))


def read_int(socket):
    """Read a bencoded integer into a Python integer."""
    return int(read_until(socket, b'e'))


def read(socket):
    """Given a socket connection, read bencode values into Python values.

    Assumes that the socket receives well-formed bencode values only."""
    first_byte = socket.recv(1)

    if first_byte == b'e':
        return None
    elif first_byte == b'd':
        return read_dict(socket)
    elif first_byte == b'l':
        return read_list(socket)
    elif first_byte == b'i':
        return read_int(socket)
    else:
        n = int(first_byte + read_until(socket, b':'))
        return socket.recv(n).decode(ENCODING)


def write_int(i):
    """Encode a Python integer as bencode."""
    return 'i{}e'.format(i)


def write_str(s):
    """Encode a Python string as a bencode byte string."""
    return '{}:{}'.format(len(s.encode(ENCODING)), s)


def write_list(l):
    """Encode a Python list as bencode."""
    s = 'l'

    for x in l:
        s += as_str(x)

    return s + 'e'


def write_dict(d):
    """Encode a Python dict as bencode."""
    s = 'd'
    ks = list(d.keys())
    ks.sort()

    for k in ks:
        s += as_str(k)
        s += as_str(d[k])

    return s + 'e'


def as_str(x):
    if isinstance(x, int):
        return write_int(x)
    elif isinstance(x, str):
        return write_str(x)
    elif isinstance(x, list):
        return write_list(x)
    elif isinstance(x, dict):
        return write_dict(x)
    else:
        raise ValueError("Can't write {} into bencode".format(x))


def write(x):
    """Encode a Python value as bencode."""
    return as_str(x).encode(ENCODING)
