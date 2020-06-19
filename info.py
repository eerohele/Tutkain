from urllib.parse import urlparse
from zipfile import ZipFile


def doc_lines(doc):
    return ['<p style="margin-top: 1rem 0;">{}</p>'.format(line) for line in doc.split('\n\n')]


def parse_location(path):
    path_parts = path.split(':')
    file_path = path_parts[0]
    line = path_parts[1]
    column = path_parts[2]

    return {'path': file_path, 'line': int(line) - 1, 'column': int(column) - 1}


def show(view, location):
    view.set_viewport_position(
        view.text_to_layout(
            view.text_point(location['line'], location['column'])
        )
    )


def goto(window, url):
    if url:
        resource = urlparse(url)

        if not resource.scheme or resource.scheme == 'file':
            location = parse_location(resource.path)

            view = window.find_open_file(location['path'])

            if not view:
                view = window.open_file(location['path'])

            show(view, location)
        elif resource.scheme == 'jar' and '!' in resource.path:
            parts = resource.path.split('!')
            jar_url = urlparse(parts[0])
            # If the path after the ! starts with a forward slash, strip it. ZipFile can't
            # find the file inside the archive otherwise.
            path = parts[1][1:] if parts[1].startswith('/') else parts[1]
            location = parse_location(path)
            archive = ZipFile(jar_url.path, 'r')
            source_file = archive.read(location['path'])

            view = window.find_open_file(location['path'])

            if view is None:
                view = window.new_file()
                view.set_name(jar_url.path + '!/' + location['path'])
                view.run_command('append', {'characters': source_file.decode()})
                view.assign_syntax('Clojure.sublime-syntax')
                view.set_scratch(True)
                view.set_read_only(True)

            show(view, location)


def show_popup(view, point, response):
    if 'info' in response:
        info = response['info']

        if 'ns' in info:
            view.show_popup(
                '''
                <body id="tutkain-lookup" style="font-size: .9rem; width: 1024px;">
                    <p style="margin: 0;">
                        <a href="{}:{}:{}"><code>{}/{}</code></a>
                    </p>
                    <p style="margin: .25rem 0 0 0;">
                        <code style="color: grey;">{}</code>
                    </p>
                    {}
                </body>'''
                .format(
                    info.get('file', ''),
                    info.get('line', ''),
                    info.get('column', ''),
                    info.get('ns', ''),
                    info.get('name', ''),
                    info.get('arglists-str', ''),
                    ''.join(doc_lines(info.get('doc', '')))),

                location=point,
                max_width=1280,
                on_navigate=lambda href: goto(view.window(), href)
            )
