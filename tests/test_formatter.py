
from unittest import TestCase

from tutkain.formatter import format


class TestFormatter(TestCase):
    def test_format(self):

        self.assertEquals(
            format({'id': 1, 'value': '2', 'ns': 'user'}),
            '2'
        )

        self.assertEquals(
            format({'id': 1, 'out': 'Hello, world!\n'}),
            ';; Hello, world!'
        )

        self.assertEquals(
            format({'in': '(+ 1 1)'}),
            ';; => (+ 1 1)'
        )

        self.assertEquals(
            format({
                'id': 1,
                'err': '''Execution error (ExceptionInfo) at user/eval96107 (REPL:1).\nBoom!\n'''
            }),
            ';; Execution error (ExceptionInfo) at user/eval96107 (REPL:1).\n;; Boom!'
        )

        self.assertEquals(
            format({
                'ex': 'class clojure.lang.ExceptionInfo',
                'status': ['eval-error'],
                'root-ex': 'class clojure.lang.ExceptionInfo',
                'id': 1,
                'nrepl.middleware.caught/throwable':
                '#error {\n :cause "Boom!"\n :data {:a 1}\n}'
            }),
            '#error {\n :cause "Boom!"\n :data {:a 1}\n}'
        )
