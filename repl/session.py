from threading import Lock


class Session():
    handlers = dict()
    errors = dict()
    namespace = 'user'

    def __init__(self, id, client, view):
        self.id = id
        self.client = client
        self.view = view
        self.op_count = 0
        self.lock = Lock()
        self.info = {}

    def supports(self, key):
        return 'ops' in self.info and key in self.info['ops']

    def set_info(self, info):
        self.info = info

    def op_id(self):
        with self.lock:
            self.op_count += 1

        return self.op_count

    def prune(self, d):
        if 'file' in d and d['file'] is None:
            del d['file']

        if 'ns' in d and d['ns'] is None:
            del d['ns']

    def op(self, d, pprint=True):
        d['session'] = self.id
        d['id'] = self.op_id()

        if d['op'] == 'eval':
            if pprint:
                d['nrepl.middleware.print/print'] = 'tutkain.nrepl.util.pprint/pprint'
                # TODO: Read wrap_width setting or the last ruler from the rulers setting?
                d['nrepl.middleware.print/options'] = {'width': 100}

            d['nrepl.middleware.caught/print?'] = 'true'
            d['nrepl.middleware.print/stream?'] = 'true'

        self.prune(d)

        return d

    def output(self, message):
        message['session'] = self.id
        self.client.recvq.put(message)

    def send(self, op, handler=None, pprint=True):
        op = self.op(op, pprint=pprint)

        if not handler:
            handler = self.client.recvq.put

        self.handlers[op['id']] = handler
        self.client.sendq.put(op)

    def handle(self, response):
        id = response.get('id')

        if 'ns' in response:
            self.namespace = response['ns']

        if not id:
            self.client.recvq.put(response)
        else:
            handler = self.handlers.get(id, self.client.recvq.put)

            try:
                handler.__call__(response)
            finally:
                if response and 'status' in response and 'done' in response['status']:
                    self.handlers.pop(id, None)
                    self.errors.pop(id, None)

    def denounce(self, response):
        id = response.get('id')

        if id:
            self.errors[id] = response

    def is_denounced(self, response):
        return response.get('id') in self.errors
