from threading import Lock


class Session():
    handlers = dict()
    errors = dict()

    def __init__(self, id, client):
        self.id = id
        self.client = client
        self.op_count = 0
        self.lock = Lock()
        self.nrepl_version = None

    def op_id(self):
        with self.lock:
            self.op_count += 1

        return self.op_count

    def supports_pretty_printing(self):
        v = self.nrepl_version
        return (v and (v.get('major') == 0 and v.get('minor') >= 8) or v.get('major') > 0)

    def op(self, d):
        d['session'] = self.id
        d['id'] = self.op_id()

        if self.supports_pretty_printing():
            d['nrepl.middleware.print/print'] = 'nrepl.util.print/pprint'

        d['nrepl.middleware.caught/print?'] = 'true'
        d['nrepl.middleware.print/stream?'] = 'true'

        if 'file' in d and d['file'] is None:
            del d['file']

        return d

    def output(self, x):
        self.client.recvq.put(x)

    def send(self, op, handler=None):
        op = self.op(op)

        if not handler:
            handler = self.client.recvq.put

        self.handlers[op['id']] = handler
        self.client.sendq.put(op)

    def handle(self, response):
        id = response.get('id')

        if id:
            handler = self.handlers.get(id, self.client.recvq.put)

            try:
                handler.__call__(response)
            finally:
                if response.get('status') == ['done']:
                    self.handlers.pop(id, None)
                    self.errors.pop(id, None)

    def denounce(self, response):
        id = response.get('id')

        if id:
            self.errors[id] = response

    def is_denounced(self, response):
        return response.get('id') in self.errors

    def terminate(self):
        self.client.halt()
