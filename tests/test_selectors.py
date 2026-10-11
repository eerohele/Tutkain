from sublime import Region

from Tutkain.src import selectors

from .util import ViewTestCase


class TestSelectors(ViewTestCase):
    def test_expand(self):
        self.set_view_content("a")
        self.assertEqual(
            selectors.expand_by_selector(self.view, 0, "meta.symbol"), Region(0, 1)
        )

        # No match at point
        self.set_view_content("a 1")
        self.assertEqual(
            selectors.expand_by_selector(self.view, 2, "meta.symbol"), None
        )

        self.set_view_content("foo/bar")
        self.assertEqual(
            selectors.expand_by_selector(
                self.view, 4, "meta.symbol - meta.namespace - punctuation.accessor"
            ),
            Region(4, 7),
        )
