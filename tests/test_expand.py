from .util import ViewTestCase
import sublime
import time
import unittesting

from Tutkain.api import edn
from Tutkain.src import settings


# Turned into a DeferrableTestCase to support tutkain_expand_selection and
# soft_undo for both regular views and panels.
#
# See https://forum.sublimetext.com/t/plugin-soft-undo/40064/4.
class TestExpandSelectionCommand(unittesting.DeferrableTestCase):
    @classmethod
    def setUpClass(self, syntax="Clojure (Tutkain).sublime-syntax"):
        sublime.run_command("new_window")
        self.view = sublime.active_window().new_file()
        self.view.set_name("tutkain.clj")
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.assign_syntax(syntax)
        settings.load().set("highlight_locals", False)

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command("close_window")

    def setUp(self):
        self.clear_view()

    def clear_view(self):
        self.view.run_command("select_all")
        self.view.run_command("right_delete")

    def set_view_content(self, chars):
        self.clear_view()
        self.view.run_command("append", {"characters": chars})

    def set_selections(self, *pairs):
        self.view.sel().clear()

        for begin, end in pairs:
            self.view.sel().add(sublime.Region(begin, end))

    def selection(self, i):
        return self.view.substr(self.view.sel()[i])

    def expand(self):
        self.view.run_command("tutkain_expand_selection")

    def shrink(self):
        self.view.run_command("soft_undo")

    def test_before_lparen(self):
        self.set_view_content("(foo)")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "(foo)" == self.selection(0)

    def test_after_lparen(self):
        self.set_view_content("(foo)")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "foo" == self.selection(0)

    def test_before_rparen(self):
        self.set_view_content("(foo)")
        self.set_selections((4, 4))
        self.expand()
        yield lambda: "foo" == self.selection(0)

    def test_after_rparen(self):
        self.set_view_content("(foo)")
        self.set_selections((6, 6))
        self.expand()
        yield lambda: "(foo)" == self.selection(0)

    def test_before_lbracket(self):
        self.set_view_content("[foo]")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "[foo]" == self.selection(0)

    def test_after_lbracket(self):
        self.set_view_content("[foo]")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "foo" == self.selection(0)

    def test_after_rbracket(self):
        self.set_view_content("[foo]")
        self.set_selections((6, 6))
        self.expand()
        yield lambda: "[foo]" == self.selection(0)

    def test_before_lcurly(self):
        self.set_view_content("{:a 1}")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "{:a 1}" == self.selection(0)

    def test_after_lcurly(self):
        self.set_view_content("{:a 1}")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: ":a" == self.selection(0)

    def test_after_rcurly(self):
        self.set_view_content("{:a 1}")
        self.set_selections((7, 7))
        self.expand()
        yield lambda: "{:a 1}" == self.selection(0)

    def test_before_set(self):
        self.set_view_content("#{1}")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "#{1}" == self.selection(0)

    def test_between_set_hash_and_bracket(self):
        self.set_view_content("#{1}")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "#{1}" == self.selection(0)

    def test_between_on_symbol(self):
        self.set_view_content("(inc 1)")
        self.set_selections((2, 2))
        self.expand()
        yield lambda: "inc" == self.selection(0)

    def test_before_at(self):
        self.set_view_content("@(foo)")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "@(foo)" == self.selection(0)

    def test_after_at(self):
        self.set_view_content("@(foo)")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "@(foo)" == self.selection(0)

    def test_after_at_rparen(self):
        self.set_view_content("@(foo)")
        self.set_selections((6, 6))
        self.expand()
        yield lambda: "@(foo)" == self.selection(0)

    def test_before_quoted_list(self):
        self.set_view_content("'(foo)")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "'(foo)" == self.selection(0)

    def test_after_quoted_list(self):
        self.set_view_content("'(foo)")
        self.set_selections((6, 6))
        self.expand()
        yield lambda: "'(foo)" == self.selection(0)

    def test_nested(self):
        self.set_view_content("(foo (bar))")
        self.set_selections((5, 5))
        self.expand()
        yield lambda: "(bar)" == self.selection(0)
        self.expand()
        yield lambda: "(foo (bar))" == self.selection(0)

    def test_before_string(self):
        self.set_view_content('(a "b" c)')
        self.set_selections((3, 3))
        self.expand()
        yield lambda: '"b"' == self.selection(0)

    def test_meta(self):
        self.set_view_content("^{:foo true}")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "^{:foo true}" == self.selection(0)
        self.set_selections((12, 12))
        self.expand()
        yield lambda: "^{:foo true}" == self.selection(0)

        self.set_view_content("^:foo")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "^:foo" == self.selection(0)
        self.set_view_content("^:foo")
        self.set_selections((5, 5))
        self.expand()
        yield lambda: "^:foo" == self.selection(0)

    def test_numbers(self):
        self.set_view_content("0.2")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "0.2" == self.selection(0)
        self.set_view_content("0.2")
        self.set_selections((3, 3))
        self.expand()
        yield lambda: "0.2" == self.selection(0)
        self.set_view_content("1/2")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "1/2" == self.selection(0)
        self.set_selections((3, 3))
        self.expand()
        yield lambda: "1/2" == self.selection(0)

    def test_string_close_paren(self):
        self.set_view_content('(a "b")')
        self.set_selections((6, 6))
        self.expand()
        yield lambda: '"b"' == self.selection(0)

    def test_qualified_map(self):
        self.set_view_content("#:foo{:bar 1} #:foo/bar{:baz 1} #::foo{:bar 1}")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "#:foo{:bar 1}" == self.selection(0)
        self.set_selections((13, 13))
        self.expand()
        yield lambda: "#:foo{:bar 1}" == self.selection(0)
        self.set_selections((14, 14))
        self.expand()
        yield lambda: "#:foo/bar{:baz 1}" == self.selection(0)
        self.set_selections((32, 32))
        self.expand()
        yield lambda: "#::foo{:bar 1}" == self.selection(0)
        self.set_selections((46, 46))
        self.expand()
        yield lambda: "#::foo{:bar 1}" == self.selection(0)
        self.set_view_content("#:foo {:bar 1}")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "#:foo {:bar 1}" == self.selection(0)

    def test_list_head(self):
        self.set_view_content("(ns foo.bar)")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "ns" == self.selection(0)

    def test_special_form(self):
        self.set_view_content("(fn [foo])")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "fn" == self.selection(0)

    def test_empty_sexp(self):
        self.set_view_content("[]")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "[]" == self.selection(0)
        self.set_view_content("()")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "()" == self.selection(0)
        self.set_view_content("{}")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: "{}" == self.selection(0)
        self.set_view_content("( )")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: " " == self.selection(0)
        self.expand()
        yield lambda: "( )" == self.selection(0)
        self.expand()
        yield lambda: "( )" == self.selection(0)
        self.set_view_content("[ (  a  ) ]")
        self.set_selections((4, 4))
        self.expand()
        yield lambda: "  a  " == self.selection(0)
        self.expand()
        yield lambda: "(  a  )" == self.selection(0)
        self.expand()
        yield lambda: "[ (  a  ) ]" == self.selection(0)

    def test_shrink(self):
        self.set_view_content("(a (b (c) d) e)")
        self.set_selections((7, 7))
        self.expand()
        yield lambda: "c" == self.selection(0)
        self.expand()
        yield lambda: "(c)" == self.selection(0)
        self.expand()
        yield lambda: "(b (c) d)" == self.selection(0)
        self.expand()
        yield lambda: "(a (b (c) d) e)" == self.selection(0)
        self.expand()
        yield lambda: "(a (b (c) d) e)" == self.selection(0)
        self.shrink()
        yield lambda: "(b (c) d)" == self.selection(0)
        self.shrink()
        yield lambda: "(c)" == self.selection(0)
        self.shrink()
        yield lambda: "c" == self.selection(0)
        self.shrink()
        yield lambda: "" == self.selection(0)
        self.shrink()
        yield lambda: "" == self.selection(0)

    def test_comment_after_open(self):
        self.set_view_content("[;;foo\n]")
        self.set_selections((0, 0))
        self.expand()
        yield lambda: "[;;foo\n]" == self.selection(0)
        self.set_selections((1, 1))
        self.expand()
        yield lambda: ";;" == self.selection(0)

    def test_issue_48(self):
        self.set_view_content("[state @state-ref]")
        self.set_selections((8, 8))
        self.expand()
        yield lambda: "@state-ref" == self.selection(0)
        self.expand()
        yield lambda: "state @state-ref" == self.selection(0)
        self.expand()
        yield lambda: "[state @state-ref]" == self.selection(0)

    def test_tagged_literal(self):
        self.set_view_content("(foo #bar/baz [:quux 1])")
        self.set_selections((5, 5))
        self.expand()
        yield lambda: "#bar/baz [:quux 1]" == self.selection(0)
        self.expand()
        yield lambda: "foo #bar/baz [:quux 1]" == self.selection(0)
        self.expand()
        yield lambda: "(foo #bar/baz [:quux 1])" == self.selection(0)

    def test_nested_tagged_literal(self):
        self.set_view_content("""(#baz/quux [#foo/bar [1]])""")

        for i in range(12, 16):
            self.set_selections((i, i))
            self.expand()
            yield lambda: """#foo/bar [1]""" == self.selection(0)

    def test_adjacent_sexp(self):
        self.set_view_content("((foo) (bar))")
        self.set_selections((8, 8))
        self.expand()
        yield lambda: "bar" == self.selection(0)
        self.expand()
        yield lambda: "(bar)" == self.selection(0)
        self.expand()
        yield lambda: "(foo) (bar)" == self.selection(0)
        self.expand()
        yield lambda: "((foo) (bar))" == self.selection(0)

    def test_macro_chars(self):
        self.set_view_content("""(a #(-> "b" c))""")
        self.set_selections((12, 12))
        self.expand()
        yield lambda: "c" == self.selection(0)
        self.expand()
        yield lambda: """-> "b" c""" == self.selection(0)
        self.expand()
        yield lambda: """#(-> "b" c)""" == self.selection(0)
        self.expand()
        yield lambda: """(a #(-> "b" c))""" == self.selection(0)

    def test_discard(self):
        self.set_view_content("""#_(:foo :bar)""")
        self.set_selections((8, 8))
        self.expand()
        yield lambda: ":bar" == self.selection(0)
        self.expand()
        yield lambda: """:foo :bar""" == self.selection(0)
        self.expand()
        yield lambda: """#_(:foo :bar)""" == self.selection(0)

    def test_existing_selection(self):
        self.set_view_content("""(-> "a" b)""")
        self.set_selections((4, 8))
        self.expand()
        yield lambda: """-> "a" b""" == self.selection(0)
        self.expand()
        yield lambda: """(-> "a" b)""" == self.selection(0)

    def test_entire_view(self):
        self.set_view_content("""(foo) (bar)""")
        self.set_selections((7, 7))
        self.expand()
        yield lambda: """bar""" == self.selection(0)
        self.expand()
        yield lambda: """(bar)""" == self.selection(0)
        self.expand()
        yield lambda: """(foo) (bar)""" == self.selection(0)

    def test_map_entry(self):
        self.set_view_content("""{:a 1 :b 2}""")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: """:a""" == self.selection(0)
        self.expand()
        yield lambda: """:a 1""" == self.selection(0)
        self.expand()
        yield lambda: """:a 1 :b 2""" == self.selection(0)
        self.expand()
        yield lambda: """{:a 1 :b 2}""" == self.selection(0)
        self.set_selections((4, 4))
        self.expand()
        yield lambda: """1""" == self.selection(0)
        self.expand()
        yield lambda: """:a 1 :b 2""" == self.selection(0)
        self.expand()
        yield lambda: """{:a 1 :b 2}""" == self.selection(0)
        self.set_view_content("""{:a [1 2]}""")
        self.set_selections((5, 5))
        self.expand()
        yield lambda: """1""" == self.selection(0)
        self.expand()
        yield lambda: """1 2""" == self.selection(0)
        self.expand()
        yield lambda: """[1 2]""" == self.selection(0)
        self.expand()
        yield lambda: """{:a [1 2]}""" == self.selection(0)
        self.set_view_content("""{#{:foo} #{:bar}}""")
        self.set_selections((11, 11))
        self.expand()
        yield lambda: """:bar""" == self.selection(0)
        self.expand()
        yield lambda: """#{:bar}""" == self.selection(0)
        self.expand()
        yield lambda: """{#{:foo} #{:bar}}""" == self.selection(0)
        self.set_view_content("""{:a}""")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: """:a""" == self.selection(0)
        self.expand()
        yield lambda: """{:a}""" == self.selection(0)
        self.set_view_content("""{{:a 1}}""")
        self.set_selections((2, 2))
        self.expand()
        yield lambda: """:a""" == self.selection(0)
        self.expand()
        yield lambda: """:a 1""" == self.selection(0)
        self.expand()
        yield lambda: """{:a 1}""" == self.selection(0)
        self.expand()
        yield lambda: """{{:a 1}}""" == self.selection(0)
        self.set_view_content("""{:a {:b :c}}""")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: """:a""" == self.selection(0)
        self.expand()
        yield lambda: """:a {:b :c}""" == self.selection(0)
        self.expand()
        yield lambda: """{:a {:b :c}}""" == self.selection(0)
        self.expand()
        yield lambda: """{:a {:b :c}}""" == self.selection(0)
        self.set_view_content("""{:a {:b :c}}""")
        self.set_selections((5, 5))
        self.expand()
        yield lambda: """:b""" == self.selection(0)
        self.expand()
        yield lambda: """:b :c""" == self.selection(0)
        self.expand()
        yield lambda: """{:b :c}""" == self.selection(0)
        self.expand()
        yield lambda: """{:a {:b :c}}""" == self.selection(0)
        self.set_view_content("""{:a {:b :c :d :e}}""")
        self.set_selections((14, 14))
        self.expand()
        yield lambda: """:e""" == self.selection(0)
        self.expand()
        yield lambda: """:b :c :d :e""" == self.selection(0)
        self.expand()
        yield lambda: """{:b :c :d :e}""" == self.selection(0)
        self.expand()
        yield lambda: """{:a {:b :c :d :e}}""" == self.selection(0)
        self.set_view_content("""{:a #{{:b :c :d :e}}}""")
        self.set_selections((16, 16))
        self.expand()
        yield lambda: """:e""" == self.selection(0)
        self.expand()
        yield lambda: """:b :c :d :e""" == self.selection(0)
        self.expand()
        yield lambda: """{:b :c :d :e}""" == self.selection(0)
        self.set_view_content("""{:a 'b}""")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: """:a""" == self.selection(0)
        self.expand()
        yield lambda: """:a 'b""" == self.selection(0)
        self.expand()
        yield lambda: """{:a 'b}""" == self.selection(0)
        self.expand()
        yield lambda: """{:a 'b}""" == self.selection(0)
        self.set_view_content("""{:a #b "c"}""")
        self.set_selections((1, 1))
        self.expand()
        yield lambda: """:a""" == self.selection(0)
        self.expand()
        yield lambda: """:a #b \"c\"""" == self.selection(0)
        self.expand()
        yield lambda: """{:a #b "c"}""" == self.selection(0)
        self.expand()
        yield lambda: """{:a #b "c"}""" == self.selection(0)
        self.set_view_content("""{:a {:b (c)}}""")
        self.set_selections((9, 9))
        self.expand()
        yield lambda: """c""" == self.selection(0)
        self.expand()
        yield lambda: """(c)""" == self.selection(0)
        self.expand()
        yield lambda: """{:b (c)}""" == self.selection(0)
        self.expand()
        yield lambda: """{:a {:b (c)}}""" == self.selection(0)

        self.set_view_content("""{[:a :b] [:c :d]}""")

        for n in range(2, 4):
            self.set_selections((n, n))
            self.expand()
            yield lambda: ":a" == self.selection(0)
            self.expand()
            yield lambda: ":a :b" == self.selection(0)

        for n in range(5, 8):
            self.set_selections((n, n))
            self.expand()
            yield lambda: ":b" == self.selection(0)
            self.expand()
            yield lambda: ":a :b" == self.selection(0)

    def test_set_in_map(self):
        self.set_view_content("""#{{:a :b}}""")
        self.set_selections((3, 3))
        self.expand()
        yield lambda: """:a""" == self.selection(0)
        self.expand()
        yield lambda: """:a :b""" == self.selection(0)
        self.expand()
        yield lambda: """{:a :b}""" == self.selection(0)
        self.expand()
        yield lambda: """#{{:a :b}}""" == self.selection(0)
