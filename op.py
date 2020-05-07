import uuid


def eval(opts):
    return {
        'op': 'eval',
        'id': str(uuid.uuid4()),
        'nrepl.middleware.caught/print?': 'true',
        'session': opts.get('session'),
        'code': opts.get('code')
    }
