from inspect import cleandoc
import sublime

from Tutkain.src import indent


from .util import ViewTestCase


class TestPruneRegion(ViewTestCase):
    def test_prune_region(self):
        self.set_view_content('( a "( b\n  ) "  )  ; (  )  c ')
        self.assertEquals(
            '(a "( b\n  ) ") ; (  )  c ',
            indent.prune_region(self.view, sublime.Region(0, self.view.size())),
        )


class TestIndentInsertNewLineCommand(ViewTestCase):
    def becomes(self, a, b, selections=[(0, 0)], newlines=1, clean=True):
        self.set_view_content(cleandoc(a) if clean else a)

        self.set_selections(*selections)

        for n in range(newlines):
            self.view.run_command("tutkain_insert_newline")

        self.assertEquals(cleandoc(b) if clean else b, self.view_content())

    def test_outside_before(self):
        self.becomes("""(foo)""", """\n\n(foo)""", newlines=2, clean=False)

    def test_outside_after(self):
        self.becomes(
            """(foo)""", """(foo)\n\n""", newlines=2, selections=[(5, 5)], clean=False
        )

    def test_inside(self):
        self.becomes(
            """
            (foo
              (bar))
            """,
            """
            (foo
            \x20\x20
              (bar))
            """,
            selections=[(4, 4)],
        )

    def test_nested_sexp_a(self):
        self.becomes(
            """
            (a (b (c)))
            """,
            """
            (a
              (b (c)))
            """,
            selections=[(2, 2)],
        )

    def test_nested_sexp_b(self):
        self.becomes(
            """
            (a
              (b (c)))
            """,
            """
            (a
              (b
                (c)))
            """,
            selections=[(7, 7)],
        )

    def test_nested_sexp_c(self):
        self.becomes(
            """
            [(foo) (bar)]
            """,
            """
            [(foo)
             (bar)]
            """,
            selections=[(6, 6)],
        )

    def test_multiple_newlines_inside(self):
        self.becomes(
            """{:a 1 :b 2}""",
            """{:a 1\n\n :b 2}""",
            selections=[(5, 5)],
            newlines=2,
            clean=False,
        )

    def test_symbol_map_vector(self):
        self.becomes(
            """{a b c d}""",
            """{a b\n c d}""",
            selections=[(4, 4)],
            clean=False,
        )
        self.becomes(
            """[a b c d]""",
            """[a b\n c d]""",
            selections=[(4, 4)],
            clean=False,
        )

    # Test cases from https://tonsky.me/blog/clojurefmt/

    def test_tonsky_1a(self):
        self.becomes(
            """
            (when something body)
            """,
            """
            (when something
              body)
            """,
            selections=[(15, 15)],
        )

    def test_tonsky_1b(self):
        self.becomes(
            """
            ( when something body)
            """,
            """
            ( when something
              body)
            """,
            selections=[(16, 16)],
        )

    def test_tonsky_2(self):
        self.becomes(
            """
            (defn f [x] body)
            """,
            """
            (defn f [x]
              body)
            """,
            selections=[(11, 11)],
        )

    def test_tonsky_2a(self):
        self.becomes(
            """
            (defn f [x] body)
            """,
            """
            (defn f
              [x] body)
            """,
            selections=[(7, 7)],
        )

    def test_tonsky_2b(self):
        self.becomes(
            """
            (defn f
              [x] body)
            """,
            """
            (defn f
              [x]
              body)
            """,
            selections=[(13, 13)],
        )

    def test_tonsky_3_many_args(self):
        self.becomes(
            """
            (defn many-args [a b c d e f]
              body)
            """,
            """
            (defn many-args [a b c
                             d e f]
              body)
            """,
            selections=[(22, 22)],
        )

    def test_tonsky_4a_multi_arity(self):
        self.becomes(
            """
            (defn multi-arity ([x] body) ([x y] body))
            """,
            """
            (defn multi-arity
              ([x] body) ([x y] body))
            """,
            selections=[(17, 17)],
        )

    def test_tonsky_4b_multi_arity(self):
        self.becomes(
            """
            (defn multi-arity
              ([x] body) ([x y] body))
            """,
            """
            (defn multi-arity
              ([x] body)
              ([x y] body))
            """,
            selections=[(30, 30)],
        )

    def test_tonsky_5(self):
        self.becomes(
            """
            (let [x 1 y 2]
              body)
            """,
            """
            (let [x 1
                  y 2]
              body)
            """,
            selections=[(9, 9)],
        )

    def test_tonsky_6(self):
        self.becomes(
            """
            [1 2 3 4 5 6]
            """,
            """
            [1 2 3
             4 5 6]
            """,
            selections=[(6, 6)],
        )

    def test_tonsky_7(self):
        self.becomes(
            """
            {:key-1 v1 :key-2 v2}
            """,
            """
            {:key-1 v1
             :key-2 v2}
            """,
            selections=[(10, 10)],
        )

    def test_tonsky_8(self):
        self.becomes(
            """
            #{a b c d e f}
            """,
            """
            #{a b c
              d e f}
            """,
            selections=[(7, 7)],
        )

    def test_multiple_cursors(self):
        self.becomes(
            """
            {:key-1 v1 :key-2 v2}

            #{a b c d e f}
            """,
            """
            {:key-1 v1
             :key-2 v2}

            #{a b c
              d e f}
            """,
            selections=[(10, 10), (30, 30)],
        )


class TestIndentRegionCommand(ViewTestCase):
    def becomes(self, a, b, selections=[(0, 0), (1, 1)]):
        self.set_view_content(cleandoc(a))
        self.set_selections(*selections)
        self.view.run_command("tutkain_indent_sexp")
        self.assertEquals(cleandoc(b), self.view_content())

    def test_1(self):
        self.becomes(
            """
            (when
            {:key-1 v1
              :key-2 v2})
            """,
            """
            (when
              {:key-1 v1
               :key-2 v2})
            """,
        )

    def test_2(self):
        self.becomes(
            """
            {:a :b

             :c :d}
            """,
            """
            {:a :b
            \x20
             :c :d}
            """,
        )

    def test_3(self):
        self.becomes(
            """
            [:a
             (when b
                c)]
            """,
            """
            [:a
             (when b
               c)]
            """,
        )

    def test_multiple_cursors(self):
        self.becomes(
            """
            {:key-1 v1
               :key-2 v2}

            #{a b c
            d e f}
            """,
            """
            {:key-1 v1
             :key-2 v2}

            #{a b c
              d e f}
            """,
            selections=[(11, 11), (30, 30)],
        )

    def test_control_keywords(self):
        self.becomes(
            """
            (try
            (/ 4 0)
            (catch Throwable t
            (println "")))
            """,
            """
            (try
              (/ 4 0)
              (catch Throwable t
                (println "")))
            """,
            selections=[(0, 0)],
        )

    def test_control_reindent(self):
        self.becomes(
            """
            (a

              )

            (b

              )
            """,
            """
            (a
            \x20\x20
              )

            (b
            \x20\x20
              )
            """,
            selections=[(3, 3), (12, 12)],
        )
