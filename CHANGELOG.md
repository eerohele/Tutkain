# Changelog

All notable changes to this project will be documented in this file.

## 0.20.0 (alpha) - TBA

- Add support for auto-completing locals (requires clojure.tools.analyzer in the classpath)
- Make auto-completion smarter in `ns` forms (requires clojure.tools.analyzer in the classpath)

  For example, given:

  ```clojure
  (ns foo.bar
    (:require []))
  ```

  When your caret is inside the square brackets, Tutkain now only suggests Clojure namespaces when auto-completing. Similarly for Java imports under.

- New connection indicator symbol
- New progress indicator
- Only show Tutkain commands that require a runtime connection in the Command Palette when actually connected to a runtime
- Improve **Tutkain: Goto Definition** history retention
- Prevent **Tutkain: ParEdit Semicolon** when typing a character literal (`\;`)
- Prevent user `*print-level*` and `*print-length*` from interfering with **Tutkain: Add Lib**
- Use simpler syntax highlighting in syntax-quoted forms

  Tutkain no longer highlights e.g. `def`, `let` etc. in syntax-quoted forms.

- Highlight sole colon (`:`) as an illegal character
- Improve interruption UX
- Include private vars when using **Tutkain: Dir**
- Add progress indicator for RPC evaluations
- Hide progress indicator on connection close #141
- Fix **Tutkain: Add Lib** compatibility with Clojure 1.12.0-alpha4 (and newer)
- Fix printing from within lazy seq when evaluating in RPC mode
- Fix syntax error exception data when evaluating in RPC mode
- Fix REPL output syntax highlighting on syntax error in RPC mode
- Fix expand selection for character literals
- Exclude native frames when exploring the stack trace using **Tutkain: Explore Stack Trace**
- Reload REPL init code every time a client connects
- Omit commas when pretty-printing evaluation results
- Fix minor pretty-printing issues
- Fix syntax definition issues with `extend-protocol`
- Fix syntax support for `\P{}` in regexps
- Fix dialect detection for Babashka `.clj` files
- Fix caret placement after **Tutkain: New Scratch View in Namespace**
- Fix clojure.repl.deps compatibility issue
- Omit uninteresting classes (such as `clojure.core$_`) from auto-completion candidates
- Minor UI improvements

## 0.19.1 (alpha) - 2023-10-10

- Fix ClojureScript evaluation result printing #125

## 0.19.0 (alpha) - 2023-10-03

- Improve evaluation result printing performance very much

- Show Java runtime version in greeting message

- Support expand/shrink selection in REPL output panel #123

- Add GitHub provider for **Tutkain: Add Lib** (with thanks to @phronmophobic!)

- Improve [exception message printing](https://clojurians.slack.com/archives/C03S1KBA2/p1683142572115519)

- Make `tutkain_paredit_forward_delete` and `tutkain_paredit_backward_delete` faster #119

- Improve the behavior of `tutkain_paredit_forward_delete` and `tutkain_paredit_backward_delete` with map namespace syntax

- Fix bad extend selection when using `tutkain_paredit_forward` or `tutkain_paredit_backward` with `"extend": true`

- Fix `output` arg support for `tutkain_evaluate` with `"scope": "input"`

- Fix `tutkain_remove_namespace_alias` when view contains no `ns` form

- Improve map namespace syntax support

- Fix bug when using `"output": "selection"` with `tutkain_evaluate` with a non-empty region selected

## 0.18.0 (alpha) - 2023-04-25

- **BREAKING** (ClojureScript): Tutkain's Babashka support now requires shadow-cljs v2.22.10 or newer

- Add support for [operating over a single connection](https://tutkain.flowthing.me/#choosing-connection-mode).

  Also see the `default_connection_mode` setting under **Tutkain: Edit Settings**.

  **Note**: This change required a complete overhaul of the shadow-cljs support. All ClojureScript connections are now locked into the RPC connection mode. (ClojureScript does not benefit from the REPL mode, since it does not support nested REPLs.)

- Add [**Tutkain: Add Lib** and **Tutkain: Synchronize Dependencies** commands](https://tutkain.flowthing.me/#working-with-dependencies).

  **Note**: These commands require Clojure v1.12.0-alpha2 or newer.

  **Note**: **Tutkain: Synchronize Dependencies** does not (yet) support aliases.

- Add support for appending the evaluation output into the current view (via the `"output": "selection"` argument).

  To use it, add a key binding like this:

  ```json
  {
    "keys": ["..."],
    "command": "tutkain_evaluate",
    "args": {"scope": "outermost", "output": "selection"},
    "context": [
      {
        "key": "selector",
        "operator": "equal",
        "operand": "source.clojure"
      }
    ]
  },
  ```

- Add the **Tutkain: Edit Settings** command

- Fix ParEdit Forward Kill form for characters #112

- Fix ParEdit Forward Delete for characters

- Fix run test when caret is on comment #106

- Fix expand selection for namespaced maps #105

- Fix auto-completion in ns with homonym alias #107

- Improve support for disabling namespace auto switching #108

- **BREAKING** (Babashka): Tutkain's Babashka support now requires Babashka v1.1.171 or newer

- Allow Babashka evaluations from files with the `.clj` extension #102

- Show reflection warnings when evaluating the entire view (via **Tutkain: Evaluate** » **View**)

- Set `*e` when evaluating the entire view throws an exception

- Show a less overwhelming error when evaluating the entire view throws an exception

- Fix **Tutkain: Remove Namespace Mapping** in views without a namespace declaration

## 0.17.0 (alpha) - 2022-10-31

- BREAKING: Tutkain no longer supports Java 8.

  Tutkain now requires Java 11 or newer.

- Improved Babashka support

  NOTE: Requires Babashka v1.0.164 or newer.

  Tutkain now supports auto-completion, var metadata lookup, clojure.test integration, **Tutkain: Apropos**, etc. when connected to a Babashka socket REPL server.

  If you cannot update Babashka to v1.0.164 or newer, pass `"backchannel" : false` when connecting to a Babashka runtime.

- Add support for `up_to_point` scope of `tutkain_evaluate` command

  Example key binding:

  ```json
  {
    "keys": ["ctrl+c", "ctrl+."],
    "command": "tutkain_evaluate",
    "args": {"scope": "up_to_point"},
    "context": [{"key": "selector", "operator": "equal", "operand": "source.clojure"}]
  },
  ```

  `up_to_point` is useful when you want to evaluate a form whose head is `->` or `->>` up to a certain point.

  For example, given that the pipe character (`|`) represents the caret, and given:

  ```clojure
  (-> 1 inc| dec)
  ```

  If you run `tutkain_evaluate` with `up_to_point` scope, Tutkain evaluates `(-> 1 inc)` instead of the entire form.

  If your caret is not inside an S-expression, `up_to_point` evaluates every top-level form up to that point. For example, given:

  ```clojure
  (inc 1)
  (inc 2)|
  (inc 3)
  ```

  If you run `tutkain_evaluate` with `up_to_point` scope, Tutkain evaluates `(inc 1)` and `(inc 2)`. This can be useful when you want to evaluate every top-level form in the namespace up to a certain point.

- Add **Tutkain: Mark Form** and `mark` scope of `tutkain_evaluate`

  To mark a form and (repeatedly) evaluate it later:

  1. Put your caret on top of a form.
  2. Run **Tutkain: Mark Form**.

  Then, to evaluate the marked form, run **Tutkain: Evaluate** > **Mark** (`tutkain_evaluate` with `"scope": "mark"`).

- Improve **Tutkain: Dir** to prompt for namespace when caret is not on symbol
- Improve keyword and symbol auto-completion support
- Add **Tutkain: Remove Namespace Mapping**, **Tutkain: Remove Namespace Alias**, and **Tutkain: Remove Namespace**

  These offer a simple UI over `ns-unmap`, `ns-unalias`, and `remove-ns` respectively.

- Fix syntax highlighting issues in deeply nested S-expressions #99
- Fix ParEdit Forward/Backward Move Form when the caret is on map value

  Previously, Tutkain moved the entire map entry when the caret was on a map
  value. Now, Tutkain only moves the map value. Tutkain still moves the entire
  map entry if the caret is on a map key.

- Allow running **Tutkain: Apropos** when the current view has a non-Clojure syntax
- Fix showing ClojureDocs examples in unloaded namespace #94
- Use relative path in `:file` meta of vars evaluated from Tutkain (for e.g. `clojure.repl/source-fn` compatibility)
- Implement ParEdit Split/Join Sexp #9
- Implement ParEdit Recenter on Sexp #9
- Prevent ParEdit from interfering with typing `\)`
- Remove invisible Unicode characters when copying text from the output view
- Fix bug when evaluating a multiline form where subsequent lines are dedented relative to the first line
- Fix Tutkain opening too many files when navigating the results of the Apropos and Dir commands
- Reduce memory consumption and improve performance of base Java class name auto-completion

  Tutkain now only auto-completes java.* and javax.* class names.

## 0.16.0 (alpha) - 2022-08-08

- Add `init` argument to `tutkain_connect`

  You can pass the fully-qualified name of a function that accepts no arguments to have Tutkain call that function when it connects to a socket server.

  For example, given:

  ```clojure
  (ns my.repl)

  (defn init
    []
    (set! *print-namespace-maps* false)
    (set! *print-length* 16)
    (set! *print-level* 8))
  ```

  You can define a key binding that looks like this:

  ```json
      {
        "keys": ["ctrl+c", "ctrl+x"],
        "command": "tutkain_connect",
        "args": {
            "init": "my.repl/init",
            // ...
        }
    },
  ```

  Then, once you connect to a socket server, Tutkain calls `my.repl/init`.

- Use panel instead of regular view when connecting via the Command Palette
- Add support for expanding the selection to map entries #97
- Improve `tutkain_paredit_thread_first` and `tutkain_paredit_thread_last`
- Add `tutkain_paredit_unthread` command

  It does the reverse of `tutkain_paredit_thread_first`/`tutkain_paredit_thread_last`.

- Fix multi-arity function syntax definition issue
- Fix pairwise movement of map entries (ParEdit)
- Fix bugs with namespace auto-switching
- Fix protocol and protocol method information lookup (`tutkain_show_information`)
- Fix bug where Tutkain would sometimes fail to update the connection status indicator in the status bar on disconnecting
- Fix syntax definition issues related to `deftype` and `defprotocol`
- Improve syntax definition, selection expansion, and ParEdit support for tagged elements
- Fix bug where Tutkain would sometimes not show the namespace of a symbol when looking up that symbol via `tutkain_show_information`
- Fix ParEdit Move Form for map entries

## 0.15.0 (alpha) - 2022-05-06

- Fix performance issues with `tutkain_insert_newline` and various ParEdit commands, especially when the caret was positioned toward the end of a long file

- Add `meta.sexp` scopes to S-expressions

  This allows you to highlight S-expression delimiters differently based on their nesting level. For example, in your color scheme you could add something like this:


  ```json
  {
    "scope": "meta.sexp punctuation.section",
    "foreground": "color(var(grey) alpha(0.5))"
  },
  {
    "scope": "meta.sexp meta.sexp punctuation.section",
    "foreground": "color(var(grey) alpha(0.6))"
  },
  {
    "scope": "meta.sexp meta.sexp meta.sexp punctuation.section",
    "foreground": "color(var(grey) alpha(0.7))"
  },
  {
    "scope": "meta.sexp meta.sexp meta.sexp meta.sexp punctuation.section",
    "foreground": "color(var(grey) alpha(0.8))"
  },
  {
    "scope": "meta.sexp meta.sexp meta.sexp meta.sexp meta.sexp punctuation.section",
    "foreground": "color(var(grey) alpha(0.9))"
  },
  ```

  S-expression delimiters would then use different shades of grey based on their nesting level.

- Add **Tutkain: New Scratch View in Namespace** command

- Add pairwise support to ParEdit Forward/Backward Move Form

  For example, given:

  ```clojure
  {:a 1 :b 2}
  ```

  And your caret is on top of `:a` or `1` and you run `tutkain_paredit_forward_move`, Tutkain will now move both the key (`:a`) and the value `1`, such that the result is:

  ```clojure
  {:b 2 :a 1}
  ```

- Fix ParEdit Forward/Backward Move Form when caret is on string

- Improve the behavior of `tutkain_paredit_forward` and `tutkain_paredit_backward` when passed `{"extend": true}`

  Tutkain now selects the entire form your caret is on.

- Fix **Tutkain: Explore Stack Trace** after error caused by loading a view

- Improve logic for determining current namespace

  Tutkain now only considers top-level `ns` or `in-ns` forms when determining the current namespace. For example, given:

  ```clojure
  (ns foo.bar)
  ```

  Tutkain will use `foo.bar` as the current namespace. Given:

  ```clojure
  (do (in-ns 'baz.quux))
  ```

  Tutkain will no longer use `baz.quux` as the current namespace.

- Synchronize view loads and other evaluations #93

- Add support for `${file}` evaluation variable

  You can now define a key binding like this, for example:

  ```json
  {
      "keys": ["ctrl+p", "ctrl+r"],
      "command": "tutkain_evaluate",
      "args": {"code": "((requiring-resolve 'cognitect.transcriptor/run) \"${file}\")"},
      "context": [{"key": "selector", "operator": "equal", "operand": "source.clojure"}]
  },
  ```

  Tutkain will replace `${file}` with the path to your current file.

- Add hyphen into `sub_word_separators`

  Moving by subwords will now stop at hyphens.

- Add namespace to ClojureScript lookup results

- Add `port: "auto"` support to `tutkain_connect`

  Setting the value of the `port` argument to `"auto"` causes Tutkain to attempt to read the port number from a file called `.repl-port` in the project root directory.

- Add support for project-specific backchannel options

  You can now add an entry like this in your Sublime Text project settings:

  ```json
  "tutkain": {
    "clojure": {
      "backchannel": {
        "port": 4321
      }
    },
  },
  ```

  Tutkain will then use port number 4321 for the backchannel in that project only.

- Add `inline_result` suport for `code` evaluations

- Add **Tutkain: Zap Commas** command

  If you have any text selected and run the command, Tutkain removes all [whitespace-commas](https://clojure.org/guides/weird_characters#_whitespace_character) in the selection. If you don't have any text selected, Tutkain removes all whitespace-commas in the current view.

## 0.14.1 (alpha) - 2022-03-14

- Reload all Python modules on package upgrade

  After this, it should no longer be necessary to restart ST after updating
  Tutkain via Package Control. In most cases, at least. Hopefully.

- If running tests via **Tutkain: Run Tests**, if the view with the tests has
  a syntax error, print the exception in the output view.

- Ensure `*err*` is flushed after eval (for `*warn-on-reflection*`) #91

- Use error symbol instead of "ERR" in status bar throughout

- Fix namespace auto-switch during long-running evaluation #92

## 0.14.0 (alpha) - 2022-03-04

- Redesign namespace auto-switching

  Previously, when you activated a Clojure view, Tutkain switched to the namespace declared in that view (or `user`/`cljs.user` if none).

  Now, Tutkain switches to the namespace declared in the current view right before evaluation.

  As before, to disable namespace auto-switching, set `auto_switch_namespace` to `false` in Tutkain's settings.

  As consequence of this and other changes in this version, Tutkain no longer
  prints the current namespace (that is, the `my.ns=> ` prompt) in the output view when you evaluate something.

  If you want to see the current namespace, you can add a key binding or [a
  custom command](https://docs.sublimetext.io/guide/extensibility/command_palette.html) that evaluates `(ns-name *ns*)`. For example:

  ```json
  {
      "keys": ["ctrl+p", "ctrl+n"],
      "command": "tutkain_evaluate",
      "args": {"code": "(ns-name *ns*)"}
  },
  ```

- Print input on the client rather than the server

  This way the user gets instant feedback on what they sent for evaluation and further improves Tutkain's compatibility with nested REPLs.

- Add gutter marks to output view

  - `>` indicates input (for example, forms you send for evaluation)
  - `<` indicates an evaluation result
  - `<<` indicates a `tap>` result (if you have `tap_panel` enabled)
  - red `<` indicates an error

- Add support for `${ns}` evaluation variable

  For example, here's a key binding that switches into the namespace in the current view:

  ```json
  {
      "keys": ["alt+a"],
      "command": "tutkain_evaluate",
      "args": {"code": "(in-ns '${ns})"},
      "context": [{
        "key": "selector",
        "operator": "equal",
        "operand": "source.clojure"
      }]
  },
  ```

- Avoid interleaving evaluation results with stderr/stdout (experimental) #86
- Fix source file name in Clojure stack traces
- Add green dot to status bar connection status indicator
- Trim extra whitespace from ClojureScript error strings
- Print test summary in status bar instead of output view
- Don't print view evaluation result in output view #85
- Disable indent guides in output view
- Add connection uptime into disconnect quick panel list
- Set output view `scroll_past_end` to 0.1

## 0.13.0 (alpha) - 2022-02-20

- Add **Tutkain: Show ClojureDocs Examples** and **Tutkain: Refresh ClojureDocs Example Cache** commands

  If your caret is on a symbol and you run **Tutkain: Show ClojureDocs Examples**, Tutkain opens a split view with ClojureDocs examples for that symbol.

  If your caret is not on a symbol, Tutkain prompts you for the name of a symbol instead.

  The first use of **Tutkain: Show ClojureDocs Examples** requires an internet connection for downloading the example data. Subsequent uses will use the data cached on your hard drive. To refresh the example data, run **Tutkain: Refresh ClojureDocs Example Cache**.

- Take `in-ns` into account when determining the current namespace

- Add `auto_show_output_panel` setting

- Fix slurping into multi-arity function body

## 0.12.0 (alpha) - 2022-01-30

- BREAKING CHANGE: Remove all default key bindings (indent on Enter, ParEdit
  key bindings for preventing unbalanced S-expression delimiters) #78

  See [this message](https://github.com/eerohele/Tutkain/blob/develop/messages/0.12.0.txt) for information on how to restore those key bindings so that
  Tutkain works the same way it did before.

- Add support for using a panel instead of a view for REPL output #79

  To use a panel instead of a view, modify the key binding for your `tutkain_connect` command to pass the `"output"` argument:

  ```json
  {
      "keys": ["ctrl+c", "ctrl+x"],
      "command": "tutkain_connect",
      "args": {"host": "localhost", "output": "panel"}
  },
  ```

  By default, Tutkain continues to use a regular view for REPL output. This is subject to change while Tutkain remains in alpha.

- Add support for copying evaluation result into your clipboard

  To use it, define a key binding like this (via **Tutkain: Edit Key Bindings**):

  ```json
  {
      "keys": ["ctrl+c", "ctrl+p"],
      "command": "tutkain_evaluate",
      "args": {"scope": "outermost", "output": "clipboard"},
      "context": [{
        "key": "selector",
        "operator": "equal",
        "operand": "source.clojure"
      }]
  },
  ```

- Add support for disabling the backchannel

  By default, when Tutkain connects to a Clojure runtime, it opens a second socket connection that it uses for tooling-related messages such as auto-completions etc.

  You can now ask Tutkain not to open that connection. To do that, define a key binding like this:

  ```json
  {
      "keys": ["ctrl+c", "ctrl+m"],
      "command": "tutkain_connect",
      "args": {
        "host": "localhost",
        "backchannel": false,
        "output": "panel"
      }
  },
  ```

- Show connection status indicator in status bar

- Fix symbol information lookup and auto-completion support when connecting to a shadow-cljs socket server without first connecting to a Clojure server

- Add **Tutkain: Choose Active Runtime** command.

  You can use it to choose which runtime to evaluate against when you use a panel for REPL output and you're connected to multiple runtimes that use the same Clojure dialect.

- Fix inline evaluation result placement
- Don't hide evaluation results when modifying the current selection #80
- Prevent errant `nil` prints when using inline evaluation results with ClojureScript
- Add `extend_comment` (default `true`) argument to the `tutkain_insert_newline`
  command

  If you set `extend_comment` to `false`, pressing Enter will no longer
  automatically insert a double semicolon at the beginning of the new line.

- Set horizontal window layout to half-and-half for code view and REPL view
- Fix `(read-line)` support
- Fix forward/backward delete for illegal `\characters`

## 0.11.0 (alpha) - 2021-11-23

- Improved support for nested clojure.main REPLs

  Evaluation results are no longer wrapped in prepl-like message frames (`{:tag ret :val ,,,}` etc.). Evaluations now send character streams and receive character streams. Standard output (`println`), exception messages, and tapped values are now sent over the same backchannel Tutkain uses for other IDE-like features (auto-completion etc.)

- Add **Tutkain: Explore Stack Trace** command

  See [Exploring exception stack traces](https://tutkain.flowthing.me/#exploring-exception-stack-traces) for more information.

- Add **Tutkain: Dir** command

  See [Listing all public vars in a namespace](https://tutkain.flowthing.me/#listing-all-public-vars-in-a-namespace).

- Add locals highlighting support for ClojureScript

- If you evaluate a view with a syntax error, show an error in the REPL view
- Tutkain now switches to the namespace in the current view after evaluating a view (via **Tutkain: Evaluate** » **View**)
- Show progress indicator when evaluating view #59
- Fix evaluation prompt

  Previously, pressing Enter would insert a line break instead of submitting the evaluation.

- Allow evaluating input when a non-Clojure view is active
- Improve auto-completion support for Java methods, fields, and classes
- Improve auto-completion UI
- Improve syntax definition for Java interop special forms
- Fix test detection error #74
- Fix lookup support for symbols that start with <
- Add `views` argument to **Tutkain: Clear Output View** (thx @perdorgirardi)

  Pass `["repl"]` to clear only the REPL view, `["tap"]` to clear only the tap panel, or `["repl", "tap"]` to clear both.

- Highlight current line when navigating unsuccessful tests via **Tutkain: Show Unsuccessful Tests** (thx @pedrorgirardi)

- Add **Tutkain: Toggle Auto Switch Namespace** command

  Namespace auto switching can interfere with nested clojure.main REPLs. You can assign a key binding to this command to temporarily disable namespace auto switching when working with nested REPLs.

  This is not a perfect solution. Suggestions welcome.

- Add **Tutkain: Prompt** command

  See [Prompting the user for evaluations](https://tutkain.flowthing.me/#prompting-the-user-for-evaluations).

- Improve shadow-cljs support backwards compatibility

  Tutkain no longer relies on the internal `shadow.cljs.devtools.server.repl-impl/do-repl` function.

- Fix prints from (`print`, `spec/explain`, `criterium/bench`, etc.) not
  showing up

- Fix **Tutkain: Apropos** result sorting
- Add **Tutkain: Loaded Libs** command
- Prevent disconnect on evaluating empty input

## 0.10.0 (alpha) - 2021-09-15

- Improve the UI of the **Tutkain: Show Unsuccessful Tests** command #65 (thx @pedrorgirardi)
- Add **Tutkain: Apropos** command
- Improve UX of **Tutkain: Show Information**

  Tutkain now no longer opens the target file in a split view.

- Fix auto-completion for top-level classes (e.g. `clojure.lang.*`)
- Fix goto definition on Windows
- Improve locals highlighting when destructuring a namespaced keyword #55
- Fix support for `tutkain_connect` `host` argument

  For example, say you specify a key binding like this:

  ```json
  {
      "keys": ["ctrl+c", "ctrl+x"],
      "command": "tutkain_connect",
      "args": {"host": "localhost"}
  },
  ```

  Then Tutkain no longer prompts you for the hostname when connecting.

- Fix doc popup arglists font
- Assign correct syntax when going to definition inside JAR (thx @pedrorgirardi!)
- A number of minor bug fixes and improvements

## 0.9.0 (alpha) - 2021-08-21

- Fix auto-completion and doc popups when connected to both Clojure and ClojureScript socket REPLs
- Add backchannel `bind_address` setting #57 (thx @dmitrydprog!)
- Use first instead of last ns form for ns auto-switch
- Avoid dangling paren after forward barf
- Optimize finding the outermost S-expression under the cursor
- Add support for highlighting/selecting locals (via the `tutkain_select_locals` command).

  Clojure only; requires [clojure.tools.analyzer.jvm](https://github.com/clojure/tools.analyzer.jvm) to be in the classpath.

- Fix errors when setting thread-bound dynamic variables in clojure.test tests #53
- Fix `:tutkain/disconnect` when printing from Clojure test
- Prevent auto-completion popup from disappearing when manually typing the entire prefix #60 (thx @dmitrydprog!)
- Add `dialect` arg to `tutkain_evaluate` command

  Instead of picking up the evaluation dialect from the currently active view, you can set it explicitly. For example:

  ```json
  {
      "keys": ["f19"],
      "command": "tutkain_evaluate",
      "args": {"ns": "user", "code": "(reset)", "dialect": "clj"},
  },
  ```

## 0.8.0 (alpha) - 2021-04-06

- Add support for shrinking selections #13 #47
- Prevent Tutkain from reindenting multiline strings
- Enable **Tutkain: Evaluate** » **Active View** for `.cljc` views
- Enable **Tutkain: Run Test Under Cursor** for `defspec`s
- Fix dialect detection for `.cljc` views
- Prevent Tutkain from evaluating empty regions
- Fix Java class/module auto-completion on Windows
- Prevent goto definition for targets whose file path is unknown
- Fix sexp detection when open bracket is immediately followed by a comment
- Fix expand selection when the caret is between `@` and a symbol
- Improve expand selection for tagged literals
- Stability improvements

## 0.7.6 (alpha) - 2021-05-26

- Restore Windows compatibility

## 0.7.5 (alpha) - 2021-05-26

- Fix Clojure REPL error when reading long forms
- Fix `tap_panel` setting

## 0.7.4 (alpha) - 2021-05-26

- Fix scratch view syntax paths
- Add ClojureScript ns symbol lookup support
- Try harder to clean up after disconnect
- Show error when connecting to a shadow-cljs build whose watch is not running
- Fix expand selection in empty S-expressions #45
- Try harder to clean up when pressing Esc in shadow-cljs build select

## 0.7.3 (alpha) - 2021-05-23

- Fix exception stack trace line and column numbers
- Don't send eval context (file, line & column) before ns switch

## 0.7.2 (alpha) - 2021-05-22

- Fix **Tutkain: Evaluate** » **Active view** return value printing

## 0.7.1 (alpha) - 2021-05-22

- Fix ClojureScript auto-completion

## 0.7.0 (alpha) - 2021-05-21

- BREAKING: Tutkain can now only connect to the [socket REPL](https://clojure.org/reference/repl_and_main#_launching_a_socket_server). It no longer supports nREPL.
- A complete rewrite of many parts of Tutkain.
- The `tutkain_evaluate_form`, `tutkain_evaluate_view`, and `tutkain_evaluate_input` commands are now deprecated. Use `tutkain_evaluate` with `scope` arg instead (see example key bindings).
- The `tutkain_run_tests_in_current_namespace` and `tutkain_run_test_under_cursor` commands are now deprecated. Use `tutkain_run_tests` with `scope` arg instead (see example key bindings).
- The `tutkain_show_symbol_information` and `tutkain_goto_symbol_definition` commands are now deprectated. Use `tutkain_show_information` and `tutkain_goto_definition` instead (see example key bindings).
- Add experimental shadow-cljs socket REPL support

    shadow-cljs only for now, until I can figure out the intricacies of getting
    a hold of the compiler environment with different ClojureScript tools.

- Add experimental Babashka socket REPL support
- Improve Java package auto-completion (Java 9+ only)
- Add support for keyword auto-completion
- Improve documentation popups
- Avoid clobbering existing window layout when connecting
- Add fdef spec info into documentation popup when available
- Add spec keyword lookup support
- Allow evaluating discarded forms
- Add `extend` arg to ParEdit Forward/Backward commands

    If `extend` is `true`, extend the current selection in addition to moving the caret.

- Add support for evaluating snippets (see documentation).
- Add :require/:import indentation compatibility mode

    If there's no newline between `:require` and the thing that immediately follows it, Tutkain will now format subsequent `:require` lines the same way. If there's a newline after `:require/:import`, Tutkain will indent the same as before. **Experimental, may be removed in the future**.

- Automatically reconnect to REPL server on startup and project load
- Fix REPL view input indentation
- Performance improvements
- Fix caret position(s) after backward slurp
- Add Forward/Backward Up/Down ParEdit commands #9
- Include whitespace when killing form
- Fix deftype/defprotocol/etc. indentation
- Improve test diffs for unsorted collections
- Fix move backward/forward inside comments
- Add Discard/Undiscard Sexp command

  It allows you to toggle whether the innermost form is discarded. That is, between `(a (b) c)` and `(a #_(b) c)` if the caret is inside `(b)`.

- Fix autocompletion in unknown namespace
- Fix minor indentation issues
- Ensure defs are in local and global symbol list
- Use clojure.pprint instead of Fipp for pretty-printing

  Mainly because of https://github.com/brandonbloom/fipp/issues/37.

- Fix indentation inside `reify`
- Disable reconnect on project load
- Update example key bindings

## 0.6.0 (alpha) - 2020-11-20
- Add the **Tutkain: Evaluate** command. Example:

    ```clojure
    {
        "keys": ["f19"],
        "command": "tutkain_evaluate",
        "args": {"ns": "user", "code": "(reset)"},
    },
    ```

- Print `:tutkain/namespace-not-found` when namespace is not found
- Print summary after **Tutkain: Run Test Under Cursor**
- Fix proxy & reify syntax definition errors
- Improve goto definition behavior #29
- Use `entity.name.variable.clojure` as def scope

## 0.5.7 (alpha) - 2020-10-15
- Fix proxy syntax definition errors
- Fix defmethod syntax definition errors
- Fix Arcadia support #31

## 0.5.6 (alpha) - 2020-10-13
- Fix Evaluate Input history support
- Add support for setting port file in project data

## 0.5.5 (alpha) - 2020-10-12
- Fix qualified symbol auto-completion

## 0.5.4 (alpha) - 2020-09-29
- Fix syntax definition errors for reify and let

## 0.5.3 (alpha) - 2020-09-28
- Fix color scheme error on package update

## 0.5.2 (alpha) - 2020-09-28
- Fix `<0x0d>` showing up in evaluation results on Windows
- Fix editing settings on Windows

## 0.5.1 (alpha) - 2020-09-28
- Add a number of default key bindings

## 0.5.0 (alpha) - 2020-09-27
- Initial alpha release
