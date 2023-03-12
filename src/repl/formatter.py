from .keywords import (
    ERR,
    OUT,
    RET,
    TAG,
    VAL,
)


# Print invisible Unicode characters (U+2063) around stdout and
# stderr to prevent them from getting syntax highlighting.
#
# This is probably somewhat evil, but the performance is *so*
# much better than with view.add_regions.
def out_string(val):
    return "⁣" + val + "⁣"


def err_string(val):
    return "⁣⁣" + val + "⁣⁣"


def format(item):
    if isinstance(item, str):
        return {TAG: RET, VAL: item.replace("\r", "")}
    elif isinstance(item, dict):
        tag = item.get(TAG)
        val = item.get(VAL, "").replace("\r", "")
        item[VAL] = val

        if tag == OUT:
            item[VAL] = out_string(val)
        elif tag == ERR:
            item[VAL] = err_string(val)

        return item
