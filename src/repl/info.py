import html
import inspect
import re
import sublime

from urllib.parse import urlparse
from zipfile import ZipFile

from ...api import edn


def show(view, line, column):
    if view is not None:
        if view.is_loading():
            sublime.set_timeout(lambda: show(view, line, column), 100)
        else:
            view.sel().clear()
            point = view.text_point(line, column)
            view.show_at_center(point)
            view.sel().add(point)


def goto(window, location):
    if location:
        resource = location["resource"]
        line = location["line"]
        column = location["column"]

        if not resource.scheme or resource.scheme == "file":
            if resource.path:
                view = window.find_open_file(resource.path)

                if not view:
                    view = window.open_file(resource.path)

                window.focus_view(view)
                show(view, line, column)
        elif resource.scheme == "jar" and "!" in resource.path:
            parts = resource.path.split("!")
            jar_url = urlparse(parts[0])
            # If the path after the ! starts with a forward slash, strip it. ZipFile can't
            # find the file inside the archive otherwise.
            path = parts[1][1:] if parts[1].startswith("/") else parts[1]
            archive = ZipFile(jar_url.path, "r")
            source_file = archive.read(path)

            view_name = jar_url.path + "!/" + path
            view = next((v for v in window.views() if v.name() == view_name), None)

            if view is None:
                view = window.new_file()
                view.set_name(view_name)
                view.run_command("append", {"characters": source_file.decode()})
                view.assign_syntax("Clojure (Tutkain).sublime-syntax")
                view.set_scratch(True)
                view.set_read_only(True)

            window.focus_view(view)
            show(view, line, column)


def parse_location(info):
    if info:
        return {
            "resource": urlparse(info.get(edn.Keyword("file"), "")),
            "line": int(info.get(edn.Keyword("line"), "1")) - 1,
            "column": int(info.get(edn.Keyword("column"), "1")) - 1,
        }


def htmlify(docstring):
    if docstring:
        doc = re.sub(
            r" ",
            "&nbsp;",
            re.sub(r"\n", "<br/>", inspect.cleandoc(html.escape(docstring.replace('\\n', '\n')))),
        )

        return f"""<p class="doc">{doc}</p>"""
    else:
        return ""


def show_popup(view, point, response):
    if edn.Keyword("info") in response:
        info = response[edn.Keyword("info")]

        if info:
            file = info.get(edn.Keyword("file"), "")
            location = parse_location(info)
            ns = info.get(edn.Keyword("ns"), "")
            symbol = info.get(edn.Keyword("name"), edn.Symbol(""))
            arglists = info.get(edn.Keyword("arglists"), "")
            fnspec = info.get(edn.Keyword("fnspec"), {})
            doc = info.get(edn.Keyword("doc"), "")

            if ns and symbol:
                symbol_name = "/".join(filter(None, [ns, symbol.name]))

                symbol = f"""
                <p class="symbol">
                    <a href="{file}">{symbol_name}</a>
                </p>
                """
            else:
                symbol = ""

            content = f"""
                <body id="tutkain-lookup">
                    <style>
                        #tutkain-lookup {{
                            font-size: .9rem;
                            padding: 0;
                            margin: 0;
                        }}

                        a {{
                            text-decoration: none;
                        }}

                        p {{
                            margin: 0;
                            padding: .25rem .5rem;
                        }}

                        .symbol, .arglists, .fnspec {{
                            border-bottom: 1px solid color(var(--foreground) alpha(0.05));
                        }}

                        .arglists, .fnspec {{
                            color: color(var(--foreground) alpha(0.5));
                        }}

                        .fnspec-key {{
                            color: color(var(--foreground) alpha(0.75));
                        }}
                    </style>
                    {symbol}"""

            if arglists:
                content += f"""<p class="arglists"><code>{arglists}</code></p>"""

            if fnspec:
                content += """<p class="fnspec">"""

                for k in [edn.Keyword("args"), edn.Keyword("ret"), edn.Keyword("fn")]:
                    if k in fnspec:
                        content += f""":<span class="fnspec-key">{k.name}</span> {fnspec[k]}<br/>"""

                content += """</p>"""

            if doc:
                content += htmlify(doc)

            content += "</body>"

            view.show_popup(
                content,
                location=point,
                max_width=1024,
                on_navigate=lambda href: goto(view.window(), location), flags=sublime.COOPERATE_WITH_AUTO_COMPLETE
            )
