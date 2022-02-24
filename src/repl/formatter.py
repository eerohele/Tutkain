from ...api import edn
from ..log import log


def value(val):
    return {"target": "view", "val": val}


def tap(val):
    return {"target": "tap", "val": val}


def clipboard(val):
    return {"target": "clipboard", "val": val}


def input(val):
    return {"target": "input", "val": val}


def inline(point, view_id, val):
    return {
        "target": "inline",
        "point": point,
        "view-id": view_id,
        "val": val
    }


# Print invisible Unicode characters (U+2063) around stdout and
# stderr to prevent them from getting syntax highlighting.
#
# This is probably somewhat evil, but the performance is *so*
# much better than with view.add_regions.
def out_string(val):
    return {"target": "view", "tag": "out", "val": '⁣' + val + '⁣'}


def err_string(val):
    return {"target": "view", "tag": "err", "val": '⁣⁣' + val + '⁣⁣'}


def format(item):
    if isinstance(item, str):
        return value(item.replace("\r", ""))
    elif isinstance(item, dict):
        tag = item.get(edn.Keyword("tag"))
        val = item.get(edn.Keyword("val"), "").replace("\r", "")

        if tag == edn.Keyword("tap"):
            return tap(val)
        elif tag == edn.Keyword("in"):
            return input(val)
        else:
            output = item.get(edn.Keyword("output"), edn.Keyword("view"))

            if output == edn.Keyword("clipboard"):
                string = val[:-1] if val[-1] == "\n" else val
                return {"target": "clipboard", "val": string}
            elif output == edn.Keyword("inline"):
                return inline(
                    item.get(edn.Keyword("point")),
                    item.get(edn.Keyword("view-id")),
                    val
                )
            else:
                if tag == edn.Keyword("err"):
                    return err_string(val)
                elif tag == edn.Keyword("out"):
                    return out_string(val)
                elif edn.Keyword("debug") in item:
                    log.debug({"event": "info", "item": item.get(edn.Keyword("val"))})
                elif val := item.get(edn.Keyword("val")):
                    return value(val)
