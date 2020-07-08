
from unittest import TestCase

from tutkain.formatter import format


class TestFormatter(TestCase):
    def test_format(self):

        self.assertEquals(
            '2',
            format({'id': 1, 'value': '2', 'ns': 'user'})
        )

        self.assertEquals(
            '=> (+ 1 2)\n',
            format({'in': '(+ 1 2)'})
        )

        self.assertEquals(
            'Hello, world!\n',
            format({'id': 1, 'out': 'Hello, world!\n'})
        )

        self.assertEquals(
            'Execution error (ExceptionInfo) at user/eval96107 (REPL:1).\nBoom!',
            format({
                'id': 1,
                'err':
                '''Execution error (ExceptionInfo) at user/eval96107 (REPL:1).
Boom!'''
            })
        )

        self.assertEquals(
            '#error {\n :cause "Boom!"\n :data {:a 1}\n}',
            format({
                'ex': 'class clojure.lang.ExceptionInfo',
                'status': ['eval-error'],
                'root-ex': 'class clojure.lang.ExceptionInfo',
                'id': 1,
                'nrepl.middleware.caught/throwable':
                '#error {\n :cause "Boom!"\n :data {:a 1}\n}'
            }),
        )
