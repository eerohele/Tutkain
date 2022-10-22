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
    def becomes(self, a, b, selections=[(0, 0)], newlines=1, clean=True, extend_comment=True):
        self.set_view_content(cleandoc(a) if clean else a)

        self.set_selections(*selections)

        for n in range(newlines):
            self.view.run_command("tutkain_insert_newline", {"extend_comment": extend_comment})

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

    def test_require_import(self):
        self.becomes(
            """
            (ns foo.bar
              (:require [baz.quux]))""",
            """
            (ns foo.bar
              (:require [baz.quux]
                        ))""",
            selections=[(34, 34)],
        )
        self.becomes(
            """
            (ns foo.bar
              (:require baz.quux))""",
            """
            (ns foo.bar
              (:require baz.quux
                        ))""",
            selections=[(32, 32)],
        )

        self.becomes(
            """
            (ns foo.bar
              (:require
               [baz.quux]))""",
            """
            (ns foo.bar
              (:require
               [baz.quux]
               ))""",
            selections=[(37, 37)],
        )

        self.becomes(
            """
            (ns foo.bar
              (:import (baz Quux)))""",
            """
            (ns foo.bar
              (:import (baz Quux)
                       ))""",
            selections=[(33, 33)],
        )

        self.becomes(
            """
            (ns foo.bar
              (:import baz.Quux))""",
            """
            (ns foo.bar
              (:import baz.Quux
                       ))""",
            selections=[(31, 31)],
        )

        self.becomes(
            """
            (ns foo.bar
              (:import
               (baz Quux)))""",
            """
            (ns foo.bar
              (:import
               (baz Quux)
               ))""",
            selections=[(36, 36)],
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

    def test_deftype(self):
        self.becomes(
            """
            (deftype Handler [] Object)
            """,
            """
            (deftype Handler []
              Object)
            """,
            selections=[(19, 19)],
        )

    def test_reify(self):
        self.becomes(
            """
            (reify Foo
              (bar [_ x]))
            """,
            """
            (reify Foo
              (bar [_ x]
                ))
            """,
            selections=[(23, 23)],
        )

    def test_extend_comment(self):
        self.becomes(
            """;; foo""",
            """;; foo\n;;\x20""",
            selections=[(6, 6)]
        )

        self.becomes(
            """;; foo""",
            """;; foo\n""",
            selections=[(6, 6)],
            extend_comment=False,
            clean=False
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

    def test_string(self):
        text = """
        (defn f
          "Example:

              (f x)
              ;;=> y
          "
          [x]
          ,,,)"""

        for n in range(63):
            self.becomes(text, text, selections=[(n, n)])

        text = """
        (defn get-foos
          [tx baz]
          (sql/query tx ["SELECT *
                          FROM [foo]
                          WHERE bar
                          NOT IN ('quux', ?);"
                         baz]))"""

        for n in range(173):
            self.becomes(text, text, selections=[(n, n)])


    def test_find_open_bracket(self):
        self.becomes(
        """
        [[:a
          :b]
        :c]""",
        """
        [[:a
          :b]
         :c]""")

        self.becomes(
        """
        [{:a :b}
         {:b :c
          :d :e}
         {:f :g}]""",
        """
        [{:a :b}
         {:b :c
          :d :e}
         {:f :g}]""")


    def test_reindent(self):
        self.assertEquals("(inc 1)", indent.reindent("(inc 1)", 0))
        self.assertEquals(
"""(inc
     1)""", indent.reindent(
"""(inc
     1)"""
, 0))

        self.assertEquals(
"""(inc
 1)""", indent.reindent(
"""(inc
 1)"""
, 0))

        self.assertEquals(
"""(inc
     1)""", indent.reindent(
"""  (inc
       1)"""
, 2))

        self.assertEquals(
"""(inc
  1)""", indent.reindent(
"""  (inc
    1)"""
, 2))
        self.assertEquals(
"""(identity
{:a 1 :b 2})""", indent.reindent(
"""    (identity
{:a 1 :b 2})"""
, 4))


class TestHardWrapCommand(ViewTestCase):
    def wraps_to(self, input, expected, width=0, start_at=0):
        self.set_view_content(input)

        for n in range(start_at, len(input)):
            self.set_selections((n, n))
            self.view.run_command("tutkain_hard_wrap", {"width": width})
            self.assertEquals(expected, self.view_content())

    def test_hard_wrap(self):
        self.wraps_to(""";; a""", """;; a""", width=5)
        self.wraps_to(""";; a b""", """;; a\n;; b""", width=5)

        # Preserves empty lines
        self.wraps_to(""";; a b\n;;\n;; c d""", """;; a\n;; b\n;;\n;; c\n;; d""", width=5)

        # Indented comment
        self.wraps_to("""  ;; a b\n  ;;\n  ;; c d""", """  ;; a\n  ;; b\n  ;;\n  ;; c\n  ;; d""", start_at=4, width=7)

        self.wraps_to("""1\n  ;; a b\n  ;;\n  ;; c d""", """1\n  ;; a\n  ;; b\n  ;;\n  ;; c\n  ;; d""", start_at=5, width=7)
        self.wraps_to("""1 ;; a b""", "1;; a\n;; b", start_at=2, width=6)
        self.wraps_to('''"a"''', '''"a"''', width=4)
        # FIXME: Fails in CI, because...?
        # self.wraps_to('''"a b c d"''', '''"a b\nc d"''', width=4)
        self.wraps_to('''"a b c d\n\ne d f g"''', '''"a b\nc d\n\ne d\nf g"''', width=4)
        self.wraps_to('''  "foo bar\n\n  baz qux"''', '''  "foo\n  bar\n\n  baz\n  qux\n  "''', start_at=2, width=7)
