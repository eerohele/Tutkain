from Tutkain.src import namespace

from .util import ViewTestCase


class TestFindDeclaration(ViewTestCase):
    def test_name(self):
        self.set_view_content("(ns foo.bar)")
        self.assertEqual("foo.bar", namespace.name(self.view))

        self.set_view_content("(ns ^:baz foo.bar)")
        self.assertEqual("foo.bar", namespace.name(self.view))

        self.set_view_content("(ns ^{:baz true} foo.bar)")
        self.assertEqual("foo.bar", namespace.name(self.view))

        self.set_view_content("(qux quux)\n(ns ^{:baz true} foo.bar)\n(zot)")
        self.assertEqual("foo.bar", namespace.name(self.view))

        # self.set_view_content('''(in-ns ^:baz 'foo.bar)\n(qux quux)''')
        # self.assertEqual(
        #     'foo.bar',
        #     namespace.name(self.view)
        # )

        self.set_view_content(
            """(ns ^{:config '{:some-keyword some-symbol}} foo.bar)"""
        )
        self.assertEqual("foo.bar", namespace.name(self.view))

        self.set_view_content("""(ns foo.bar) (ns baz.quux)""")
        self.assertEqual("foo.bar", namespace.name(self.view))

        self.set_view_content("""(do (in-ns 'foo.bar))""")
        self.assertEqual(None, namespace.name(self.view))

        self.set_view_content("""(do (ns foo.bar))""")
        self.assertEqual(None, namespace.name(self.view))
