from functools import partial


def read_until(socket, terminator):
    bs = bytearray()

    for byte in iter(partial(socket.recv, 1), terminator):
        bs.extend(byte)

    return bs


def read_list(socket, acc):
    datum = read(socket)

    if datum is None:
        return acc
    else:
        acc.append(datum)
        return read_list(socket, acc)


def into_dict(l):
    return {l[i]: l[i + 1] for i in range(0, len(l), 2)}


def read_dict(socket, acc):
    return into_dict(read_list(socket, acc))


def read_int(socket):
    return int(read_until(socket, b'e'))


def read(socket):
    first_byte = socket.recv(1)

    if first_byte == b'e':
        return None
    elif first_byte == b'd':
        return read_dict(socket, [])
    elif first_byte == b'l':
        return read_list(socket, [])
    elif first_byte == b'i':
        return read_int(socket)
    else:
        n = int(first_byte + read_until(socket, b':'))
        return socket.recv(n).decode('utf-8')


def write_int(i):
    return 'i{}e'.format(i)


def write_str(s):
    return '{}:{}'.format(len(s), s)


def write_list(l):
    s = 'l'

    for x in l:
        s += as_str(x)

    return s + 'e'


def write_dict(d):
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
    return str.encode(as_str(x), encoding='utf-8')
