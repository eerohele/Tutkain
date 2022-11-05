from unittest import TestCase

import sublime

from Tutkain.api import edn
from Tutkain.src.repl import views


class TestConfigure(TestCase):
    def setUp(self):
        self.window = sublime.active_window()
        self.repl_view = self.window.new_file()

    def tearDown(self):
        if self.repl_view:
            self.repl_view.close()

    def configure(self, settings):
        return views.configure(
            self.repl_view,
            edn.Keyword("clj"),
            "1",
            "localhost",
            1234,
            settings,
        )

    def test_configure(self):
        # Test default settings:

        configured_view = self.configure({})

        # All view settings available in default settings must match,
        # since we passed an empty dict for settings overwrites.
        for settings_name, settings_value in (
            configured_view.settings().to_dict().items()
        ):
            if settings_name in views.REPL_VIEW_DEFAULT_SETTINGS:
                self.assertEquals(
                    views.REPL_VIEW_DEFAULT_SETTINGS[settings_name], settings_value
                )

        # Test user overwrites:

        configured_view = self.configure(
            {
                "word_wrap": False,
                "font_size": 11,
                "scroll_past_end": 1,
            },
        )

        # View settings must match the settings passed to configure:

        self.assertEquals(11, configured_view.settings().get("font_size"))
        self.assertEquals(False, configured_view.settings().get("word_wrap"))
        self.assertEquals(1, configured_view.settings().get("scroll_past_end"))

        # Test internal settings overwrites:

        configured_view = self.configure(
            {
                "tutkain_repl_view_dialect": "foo",
                "tutkain_repl_host": "bar",
                "tutkain_repl_port": "baz",
            },
        )

        # Internal settings can't be overwritten by the user,
        # so the provided settings above doesn't matter:

        self.assertEquals(
            "clj", configured_view.settings().get("tutkain_repl_view_dialect")
        )
        self.assertEquals(
            "localhost", configured_view.settings().get("tutkain_repl_host")
        )
        self.assertEquals(1234, configured_view.settings().get("tutkain_repl_port"))
