from urllib.parse import urlparse
from zipfile import ZipFile


def doc_lines(doc):
    return [
        '<p style="margin-top: 1rem 0;">{}</p>'.format(line) for line in doc.split('\n\n') if line
    ]


def show(view, line, column):
    view.set_viewport_position(
        view.text_to_layout(
            view.text_point(line, column)
        )
    )


def goto(window, location):
    if location:
        resource = location['resource']
        line = location['line']
        column = location['column']

        if not resource.scheme or resource.scheme == 'file':
            view = window.find_open_file(resource.path)

            if not view:
                view = window.open_file(resource.path)

            show(view, line, column)
        elif resource.scheme == 'jar' and '!' in resource.path:
            parts = resource.path.split('!')
            jar_url = urlparse(parts[0])
            # If the path after the ! starts with a forward slash, strip it. ZipFile can't
            # find the file inside the archive otherwise.
            path = parts[1][1:] if parts[1].startswith('/') else parts[1]
            archive = ZipFile(jar_url.path, 'r')
            source_file = archive.read(path)

            view_name = jar_url.path + '!/' + path
            view = next((v for v in window.views() if v.name() == view_name), None)

            if view is None:
                view = window.new_file()
                view.set_name(view_name)
                view.run_command('append', {'characters': source_file.decode()})
                view.assign_syntax('Clojure.sublime-syntax')
                view.set_scratch(True)
                view.set_read_only(True)

            window.focus_view(view)
            show(view, line, column)


def parse_location(info):
    if info:
        return {'resource': urlparse(info.get('file', '')),
                'line': int(info.get('line', '1')) - 1,
                'column': int(info.get('column', '1')) - 1}


def show_popup(view, point, response):
    if 'info' in response:
        info = response['info']

        if 'ns' in info:
            file = info.get('file', '')
            location = parse_location(info)
            ns = info.get('ns', '')
            name = info.get('name', '')
            arglists = info.get('arglists-str', '')
            doc = ''.join(doc_lines(info.get('doc', '')))

            view.show_popup(
                '''
                <body id="tutkain-lookup" style="font-size: .9rem; width: 1024px;">
                    <p style="margin: 0;">
                        <a href="{}"><code>{}/{}</code></a>
                    </p>
                    <p style="margin: 0;">
                        <code style="color: grey;">{}</code>
                    </p>
                    {}
                </body>'''
                .format(file, ns, name, arglists, doc),
                location=point,
                max_width=1280,
                on_navigate=lambda href: goto(view.window(), location)
            )
