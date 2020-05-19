def format_out(out):
    # TODO: Why do I need to do this?
    maybe_newline = '\n' if out.endswith('\n') else ''

    return '\n'.join(
        map(lambda line: ';; {}'.format(line), out.splitlines())
    ) + maybe_newline


def format(message):
    if 'value' in message:
        return message['value']
    if 'nrepl.middleware.caught/throwable' in message:
        return message.get('nrepl.middleware.caught/throwable')
    if 'out' in message:
        return format_out(message['out'])
    if 'append' in message:
        return message['append']
    if 'err' in message:
        return format_out(message.get('err'))
    if 'versions' in message:
        versions = message.get('versions')

        clojure_version = versions.get('clojure').get('version-string')
        nrepl_version = versions.get('nrepl').get('version-string')

        return format_out(
            'Clojure {}\nnREPL {}'.format(clojure_version, nrepl_version)
        ) + '\n'
