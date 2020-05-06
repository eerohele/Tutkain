import sublime
import socket

from unittest import TestCase

import tutkain.tutkain as tutkain
import tutkain.brackets as brackets
import tutkain.bencode as bencode


# NOTE: Before you run these tests, you must:
#
# 1. Start a TCP echo server at localhost:4321:
#
#        $ ncat -l 4321 --keep-open --exec "/bin/cat"
#
# 2. Start an nREPL server at localhost:1234:
#
#        $ cd tests/fixtures
#        $ clojure -m nrepl.cmdline --port 1234
#
# TODO: It would be nice if we didn't have to do either of these things.
class TestBencode(TestCase):
    server = None
    client = None

    def setUp(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect(('localhost', 4321))

    def tearDown(self):
        if self.client is not None:
            self.client.shutdown(socket.SHUT_RDWR)
            self.client.close()

    def test_read_int(self):
        self.client.sendall(b'i42e')
        self.assertEquals(bencode.read(self.client), 42)
        self.client.sendall(b'i0e')
        self.assertEquals(bencode.read(self.client), 0)
        self.client.sendall(b'i-42e')
        self.assertEquals(bencode.read(self.client), -42)

    def test_read_byte_string(self):
        self.client.sendall(b'4:spam')
        self.assertEquals(bencode.read(self.client), 'spam')

    def test_read_list(self):
        self.client.sendall(b'l4:spami42ee')
        self.assertEquals(bencode.read(self.client), ['spam', 42])

    def test_read_dict(self):
        self.client.sendall(b'd3:bar4:spam3:fooi42ee')
        self.assertEquals(
            bencode.read(self.client),
            {'foo': 42, 'bar': 'spam'}
        )

    def test_write_str(self):
        self.assertEquals(
            bencode.write('Hello, world!'),
            b'13:Hello, world!'
        )

    def test_write_int(self):
        self.assertEquals(
            bencode.write(42),
            b'i42e'
        )

    def test_write_list(self):
        self.assertEquals(
            bencode.write(['spam', 42]),
            b'l4:spami42ee'
        )

    def test_write_dict(self):
        self.assertEquals(
            bencode.write({'foo': 42, 'bar': 'spam'}),
            b'd3:bar4:spam3:fooi42ee'
        )


class TestReplClient(TestCase):
    def test_repl_client(self):
        with tutkain.ReplClient('localhost', 1234) as repl_client:
            repl_client.input.put({
                'op': 'eval',
                'session': repl_client.session,
                'code': '(+ 1 2 3)'
            })

            versions = repl_client.output.get().get('versions')
            nrepl_version = versions.get('nrepl').get('version-string')
            clojure_version = versions.get('clojure').get('version-string')

            self.assertEquals(nrepl_version, '0.7.0')
            self.assertEquals(clojure_version, '1.10.1')
            self.assertEquals(repl_client.output.get().get('value'), '6')


class TestBrackets(TestCase):
    def setUp(self):
        self.view = sublime.active_window().new_file()
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.set_syntax_file('Packages/Clojure/Clojure.tmLanguage')

    def tearDown(self):
        if self.view:
            self.view.window().run_command('close_file')

    def set_view_content(self, chars):
        self.view.run_command('append', {'characters': chars})

    def form(self, pos):
        return self.view.substr(brackets.current_form_region(self.view, pos))

    def test_current_form_region_simple(self):
        form = '(+ 1 2)'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_brackets(self):
        form = '[1 [2 3] 4]'
        self.set_view_content(form)
        self.assertEquals(self.form(0), form)
        self.assertEquals(self.form(len(form)), form)
        self.assertEquals(self.form(3), '[2 3]')

    def test_current_form_region_mixed(self):
        form = '(a {:b :c} [:d] )'
        self.set_view_content(form)
        self.assertEquals(self.form(5), '{:b :c}')
        self.assertEquals(self.form(11), '[:d]')
        self.assertEquals(self.form(16), form)

    def test_current_form_region_set(self):
        form = '#{1 2 3}'
        self.set_view_content(form)
        for n in range(len(form)):
            self.assertEquals(self.form(n), form)

    def test_current_form_region_discard(self):
        form = '(inc #_(dec 2) 4)'
        self.set_view_content(form)
        self.assertEquals(self.form(7), '(dec 2)')
        self.assertEquals(self.form(12), '(dec 2)')
        self.assertEquals(self.form(12), '(dec 2)')
        self.assertEquals(self.form(14), '(dec 2)')
        self.assertEquals(self.form(16), form)

    def test_string_next_to_lbracket(self):
        form = '(merge {"A" :B})'
        self.set_view_content(form)
        self.assertEquals(self.form(len(form)), form)

    def test_ignore_string_1(self):
        form = '(a "()" b)'
        self.set_view_content(form)
        self.assertEquals(self.form(len(form)), form)

    def test_ignore_string_2(self):
        form = '(a "\"()\"" b)'
        self.set_view_content(form)
        self.assertEquals(self.form(len(form)), form)
