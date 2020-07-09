def format(message):
    if 'value' in message:
        return message['value']
    if 'tap' in message:
        return message['tap']
    if 'nrepl.middleware.caught/throwable' in message:
        return message.get('nrepl.middleware.caught/throwable')
    if 'out' in message:
        return message['out']
    if 'in' in message:
        ns = message.get('ns') or ''
        return '{}=> {}\n'.format(ns, message['in'])
    if 'err' in message:
        return message.get('err')
    if 'versions' in message:
        versions = message.get('versions')

        clojure_version = versions.get('clojure')
        nrepl_version = versions.get('nrepl')
        babashka_version = versions.get('babashka')

        if clojure_version and nrepl_version:
            return (
                '''Clojure {}\nnREPL {}\n'''.format(
                    clojure_version.get('version-string'), nrepl_version.get('version-string')
                )
            )
        elif babashka_version:
            return (
                '''Babashka {}\nbabashka.nrepl {}\n'''.format(
                    babashka_version,
                    versions.get('babashka.nrepl')
                )
            )
