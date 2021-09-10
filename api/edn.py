"""An implementation of Extensible Data Notation (EDN).

This implementation is incomplete. There's just enough so that the Python
plugin host can communicate with the Clojure server.

The tricky parts are ported from Clojure's EdnReader.java.

For more information on EDN, see https://github.com/edn-format/edn."""

from dataclasses import dataclass
import io


# Types


@dataclass(eq=True, frozen=True)
class Keyword:
    name: str
    namespace: str = ""

    def __repr__(self):
        if self.namespace:
            return f":{self.namespace}/{self.name}"
        else:
            return f":{self.name}"


@dataclass(eq=True, frozen=True)
class Symbol:
    name: str
    namespace: str = ""

    def __repr__(self):
        if self.namespace:
            return f"{self.namespace}/{self.name}"
        else:
            return f"{self.name}"


def kwmap(d):
    """Given a Python dictionary, return a copy of the dictionary with the
    top-level keys transformed into EDN keywords."""
    return {Keyword(k): v for k, v in d.items()}


# Read


def error(error, b, ch):
    raise error(b.getvalue(), b.tell(), ch)


def unread(b, n):
    """Given a file object and an integer, unread that many characters from
    the object."""
    b.seek(b.tell() - n)


def read_string(b, _):
    """Given a file object, read a single EDN string."""
    with io.StringIO() as s:
        while (ch := b.read(1)) != '"':
            if ch == "\\":
                ch = b.read(1)

                if ch == "t":
                    ch = "\t"
                elif ch == "n":
                    ch = "\n"
                elif ch == "r":
                    ch = ""

            s.write(ch)

        return s.getvalue()


def read_comment(b, ch):
    error(NotImplementedError, b, ch)


def read_meta(b, ch):
    error(NotImplementedError, b, ch)


def read_list(b, _):
    """Given a file object, read a single EDN list."""
    return read_delimited_list(b, ')')


def read_delimited_list(b, delim):
    """Given a file object and a delimiter character, read an EDN element
    that edns with that character."""
    xs = []

    while (ch := b.read(1)) != delim:
        if is_whitespace(ch):
            continue

        xs.append(read1(b, ch))

    return xs


def read_vector(b, _):
    """Given a file object, read a single EDN vector."""
    return read_delimited_list(b, ']')


def read_set(b, _):
    """Given a file object, read a single EDN set."""
    return set(read_delimited_list(b, '}'))


class UnmatchedDelimiterError(ValueError):
    pass


def read_unmatched_delimiter(b, ch):
    error(UnmatchedDelimiterError, b, ch)


def read_map(b, _):
    """Given a file object, read a single EDN map."""
    xs = read_delimited_list(b, '}')

    if (len(xs) & 1) == 1:
        raise ValueError("Map must have an even number of elements")

    it = iter(xs)
    return dict(zip(it, it))


def read_character(b, _):
    """Given a file object, read a single EDN character."""
    ch = b.read(1)
    token = read_token(b, ch)

    if len(token) == 1:
        return token
    elif token == "space":
        return " "
    elif token == "tab":
        return "\t"
    elif token in {"newline", "return"}:
        return "\n"
    else:
        error(NotImplementedError, b, ch)


def read_dispatch(b, ch):
    """Given a file object and a character, read an EDN element prefixed by the
    dispatch macro."""
    x = b.read(1)

    if x == '{':
        return read_set(b, ch)
    else:
        error(NotImplementedError, b, ch)


# https://github.com/clojure/clojure/blob/ecd5ff59e07de649a9f9affb897d02165fe7e553/src/jvm/clojure/lang/EdnReader.java#L37-L59
MACROS = {
    '"': read_string,
    ';': read_comment,
    '^': read_meta,
    '(': read_list,
    ')': read_unmatched_delimiter,
    '[': read_vector,
    ']': read_unmatched_delimiter,
    '{': read_map,
    '}': read_unmatched_delimiter,
    '\\': read_character,
    '#': read_dispatch
}


def read_macro(b, ch):
    """Read an EDN element prefixed by a macro character.

    A macro character is one of:

    - string
    - comment
    - metadata
    - list
    - vector
    - map
    - character
    - dispatch"""
    return MACROS.get(ch, lambda _1, _2: None).__call__(b, ch)


def is_whitespace(ch):
    """Given a character, return true if it's an EDN whitespace character."""
    return ch == "," or ch.isspace()


def is_macro(ch):
    """Given a character, return true if it's a macro character."""
    return ch in MACROS


def is_terminating_macro(ch):
    """Given a character, return true if it's a terminating macro.

    A terminating macro signifies the end of an EDN token."""
    return (ch != "#" and ch != "'" and is_macro(ch))


def read_token(b, ch):
    """Given a file object and a start character, read a single EDN token."""
    with io.StringIO() as s:
        s.write(ch)

        while ch := b.read(1):
            if is_whitespace(ch) or is_terminating_macro(ch):
                unread(b, 1)
                break

            s.write(ch)

        return s.getvalue()


def read_number(b, ch):
    """Given a file object and a start character, read a single number."""
    with io.StringIO() as s:
        s.write(ch)

        while x := b.read(1):
            if not x.isdigit():
                unread(b, 1)
                break

            s.write(x)

        return int(s.getvalue())


def interpret_token(token):
    """Interpret an EDN token.

    A token in this context is one of:

    - nil
    - true/false
    - keyword
    - symbol"""
    if token == "nil":
        return None
    elif token == "true":
        return True
    elif token == "false":
        return False
    elif token.startswith(":"):
        xs = token.split("/")

        if len(xs) == 2:
            return Keyword(xs[1], xs[0][1:])
        else:
            return Keyword(xs[0][1:])
    else:
        return Symbol(token)


def read1(b, ch):
    """Given a file object and a start character, read one EDN element from the
    file object."""
    while is_whitespace(ch):
        ch = b.read(1)

    if ch.isdigit():
        return read_number(b, ch)
    elif is_macro(ch):
        return read_macro(b, ch)
    else:
        return interpret_token(read_token(b, ch))


def read(s):
    """Read one EDN element from a string."""
    with io.StringIO(s) as s:
        return read1(s, s.read(1))


def read_line(b):
    """Read one line of EDN from the given file object."""
    if line := b.readline():
        return read(line)


# Write


def write_nil(b, _):
    b.write("nil")


def write_bool(b, x):
    b.write("true" if x else "false")


def write_int(b, x):
    b.write(str(x))


def write_str(b, x):
    b.write("\"")
    # FIXME: Quick 'n' dirty. What if there's more backslashes? Regular
    # expressions or loop over string
    b.write(x.replace('\\', '\\\\').replace('"', '\\"'))
    b.write("\"")


def write_keyword(b, x):
    b.write(":")

    if x.namespace:
        b.write(x.namespace + "/")

    b.write(x.name)


def write_symbol(b, x):
    if x.namespace:
        b.write(x.namespace + "/")

    b.write(x.name)


def write_list(b, xs):
    b.write("[")

    if xs:
        for x in xs[:-1]:
            write1(b, x)
            b.write(", ")

        write1(b, xs[-1])

    b.write("]")


def write_set(b, xs):
    b.write("#{")

    for x in xs:
        write1(b, x)
        b.write(",")

    b.write("}")


def write_dict(b, d):
    b.write("{")

    xs = list(d.items())

    for k, v in xs[:-1]:
        write1(b, k)
        b.write(" ")
        write1(b, v)
        b.write(" ")

    write1(b, xs[-1][0])
    b.write(" ")
    write1(b, xs[-1][1])

    b.write("}")


def write1(b, x):
    if x is None:
        write_nil(b, x)
    elif isinstance(x, bool):
        write_bool(b, x)
    elif isinstance(x, int):
        write_int(b, x)
    elif isinstance(x, str):
        write_str(b, x)
    elif isinstance(x, Keyword):
        write_keyword(b, x)
    elif isinstance(x, Symbol):
        write_symbol(b, x)
    elif isinstance(x, set):
        write_set(b, x)
    elif isinstance(x, list):
        write_list(b, x)
    elif isinstance(x, dict):
        write_dict(b, x)
    else:
        raise ValueError(f"""Can't write {x} as EDN""")


def write(b, x):
    write1(b, x)
    b.write("\n")
    b.flush()
