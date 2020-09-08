from Tutkain.src import namespace

from .util import ViewTestCase


class TestFindDeclaration(ViewTestCase):
    def test_find_declaration(self):
        self.set_view_content("(ns foo.bar)")
        self.assertEquals("foo.bar", namespace.find_declaration(self.view))

        self.set_view_content("(ns ^:baz foo.bar)")
        self.assertEquals("foo.bar", namespace.find_declaration(self.view))

        self.set_view_content("(ns ^{:baz true} foo.bar)")
        self.assertEquals("foo.bar", namespace.find_declaration(self.view))

        self.set_view_content("(qux quux)\n(ns ^{:baz true} foo.bar)\n(zot)")
        self.assertEquals("foo.bar", namespace.find_declaration(self.view))

        # self.set_view_content('''(in-ns ^:baz 'foo.bar)\n(qux quux)''')
        # self.assertEquals(
        #     'foo.bar',
        #     namespace.find_declaration(self.view)
        # )

        self.set_view_content(
            """(ns ^{:config '{:some-keyword some-symbol}} foo.bar)"""
        )
        self.assertEquals("foo.bar", namespace.find_declaration(self.view))
