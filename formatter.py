def format(message):
    if 'value' in message:
        return message['value']
    if 'nrepl.middleware.caught/throwable' in message:
        return message.get('nrepl.middleware.caught/throwable')
    if 'out' in message:
        return message['out']
    if 'in' in message:
        ns = message.get('ns') or ''
        return '{}=> {}\n'.format(ns, message['in'])
    if 'append' in message:
        return message['append']
    if 'err' in message:
        return message.get('err')
    if 'versions' in message:
        versions = message.get('versions')

        clojure_version = versions.get('clojure').get('version-string')
        nrepl_version = versions.get('nrepl').get('version-string')

        return (
            '''Clojure {}\nnREPL {}\n'''.format(clojure_version, nrepl_version)
        )
