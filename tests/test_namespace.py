from Tutkain.src import namespace

from .util import ViewTestCase


class TestFindDeclaration(ViewTestCase):
    def test_name(self):
        self.set_view_content("(ns foo.bar)")
        self.assertEquals("foo.bar", namespace.name(self.view))

        self.set_view_content("(ns ^:baz foo.bar)")
        self.assertEquals("foo.bar", namespace.name(self.view))

        self.set_view_content("(ns ^{:baz true} foo.bar)")
        self.assertEquals("foo.bar", namespace.name(self.view))

        self.set_view_content("(qux quux)\n(ns ^{:baz true} foo.bar)\n(zot)")
        self.assertEquals("foo.bar", namespace.name(self.view))

        # self.set_view_content('''(in-ns ^:baz 'foo.bar)\n(qux quux)''')
        # self.assertEquals(
        #     'foo.bar',
        #     namespace.name(self.view)
        # )

        self.set_view_content(
            """(ns ^{:config '{:some-keyword some-symbol}} foo.bar)"""
        )
        self.assertEquals("foo.bar", namespace.name(self.view))

        self.set_view_content(
            """(ns foo.bar) (ns baz.quux)"""
        )
        self.assertEquals("foo.bar", namespace.name(self.view))

        self.set_view_content(
            """(do (in-ns 'foo.bar))"""
        )
        self.assertEquals(None, namespace.name(self.view))

        self.set_view_content(
            """(do (ns foo.bar))"""
        )
        self.assertEquals(None, namespace.name(self.view))
