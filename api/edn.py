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


# Read


def unread(b, n):
    b.seek(b.tell() - n)


def read_string(b, _):
    with io.StringIO() as s:
        while (ch := b.read(1)) != '"':
            if ch == "\\":
                ch = b.read(1)

                if ch == "t":
                    ch = "\t"
                elif ch in {"n", "r"}:
                    ch = "\n"

            s.write(ch)

        return s.getvalue()


def read_comment(b, ch):
    raise NotImplementedError()


def read_meta(b, ch):
    raise NotImplementedError()


def read_list(b, ch):
    return read_delimited_list(b, ')')


def read_delimited_list(b, delim):
    xs = []

    while (ch := b.read(1)) != delim:
        if is_whitespace(ch):
            continue

        xs.append(read1(b, ch))

    return xs


def read_vector(b, ch):
    return read_delimited_list(b, ']')


def read_set(b, ch):
    return set(read_delimited_list(b, '}'))


class UnmatchedDelimiterError(ValueError):
    pass


def read_unmatched_delimiter(b, ch):
    raise UnmatchedDelimiterError(b.getvalue(), b.tell(), ch)


def read_map(b, ch):
    xs = read_delimited_list(b, '}')

    if (len(xs) & 1) == 1:
        raise ValueError("Map must have an even number of elements")

    it = iter(xs)
    return dict(zip(it, it))


def read_character(b, ch):
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
        raise NotImplementedError(ch, token)


def read_dispatch(b, ch):
    x = b.read(1)

    if x == '{':
        return read_set(b, ch)
    else:
        raise NotImplementedError()


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
    return MACROS.get(ch, lambda _1, _2: None).__call__(b, ch)


def is_whitespace(ch):
    return ch == "," or ch.isspace()


def is_macro(ch):
    return ch in MACROS


def is_terminating_macro(ch):
    return (ch != "#" and ch != "'" and is_macro(ch))


def read_token(b, ch):
    with io.StringIO() as s:
        s.write(ch)

        while ch := b.read(1):
            if is_whitespace(ch) or is_terminating_macro(ch):
                unread(b, 1)
                break

            s.write(ch)

        return s.getvalue()


def read_number(b, ch):
    with io.StringIO() as s:
        s.write(ch)

        while x := b.read(1):
            if not x.isdigit():
                unread(b, 1)
                break

            s.write(x)

        return int(s.getvalue())


def interpret_token(token):
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
    while is_whitespace(ch):
        ch = b.read(1)

    if ch.isdigit():
        return read_number(b, ch)
    elif is_macro(ch):
        return read_macro(b, ch)
    else:
        return interpret_token(read_token(b, ch))


def read(s):
    with io.StringIO(s) as s:
        return read1(s, s.read(1))


def read_line(b):
    if line := b.readline():
        return read(line)


# Write


def write_nil(b, x):
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
