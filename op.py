import uuid


def eval(opts):
    return {
        'op': 'eval',
        'id': str(uuid.uuid4()),
        'nrepl.middleware.print/print': 'clojure.pprint/write',
        'session': opts.get('session'),
        'code': opts.get('code')
    }
