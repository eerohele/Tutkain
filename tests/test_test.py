from functools import partial
from .util import ViewTestCase
from Tutkain.src import test


class TestTest(ViewTestCase):
    def assertAlwaysYields(self, content, expected, producer):
        self.set_view_content(content)

        for n in range(len(content)):
            self.assertEquals(expected, producer(n), n)

    def test_current(self):
        current = partial(test.current, self.view)

        self.assertAlwaysYields('(deftest foo)', 'foo', current)
        self.assertAlwaysYields('(deftest ^:foo bar)', 'bar', current)

        self.set_view_content('(doseq (deftest ^:foo bar))')
        self.assertEquals(None, test.current(self.view, 6))
        self.assertEquals('bar', test.current(self.view, 7))
        self.assertEquals('bar', test.current(self.view, 26))
        self.assertEquals(None, test.current(self.view, 27))
