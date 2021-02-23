# Changelog
All notable changes to this project will be documented in this file.

## Unreleased
- Add support for keyword auto-completion

  Requires nREPL 0.9.0 or newer, which has not yet been released at the time of this release.

- Improve documentation popup
- Improve sideloader error tolerance

  This allows Tutkain to connect to nREPL servers that run in environments where the nREPL sideloader cannot write temporary files.

- Avoid clobbering existing window layout
- Add :require/:import indentation compatibility mode

    If there's no newline between `:require` and the thing that immediately follows it, Tutkain will now format subsequent `:require` lines the same way. If there's a newline after `:require/:import`, Tutkain will indent the same as before. **Experimental, may be removed in the future**.

- Automatically reconnect to nREPL server on startup and project load
- Fix REPL view input indentation
- Performance improvements
- Fix caret position(s) after backward slurp
- Add Forward/Backward Up/Down ParEdit commands #9
- Include whitespace when killing form
- Fix deftype/defprotocol/etc. indentation
- Fix file, line, and column info in exception stack traces
- Clean up exception stack traces
- Improve test diffs for unsorted collections
- Fix move backward/forward inside comments
- Add Discard/Undiscard Sexp command

  It allows you to toggle whether the innermost form is discarded. That is, between `(a (b) c)` and `(a #_(b) c)` if the caret is inside `(b)`.

- Fix autocompletion in unknown namespace
- Fix minor indentation issues
- Ensure defs are in local and global symbol list
- Improve ParEdit Backward/Forward Kill behavior
- Use clojure.pprint instead of Fipp for pretty-printing

  Mainly because of https://github.com/brandonbloom/fipp/issues/37.

  I'll try to make it easy to use Fipp instead of clojure.pprint for those who want to.

- Fix indentation inside `reify`

## 0.6.0 - 2020-11-20
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

## 0.5.7 - 2020-10-15
- Fix proxy syntax definition errors
- Fix defmethod syntax definition errors
- Fix Arcadia support #31

## 0.5.6 - 2020-10-13
- Fix Evaluate Input history support
- Add support for setting port file in project data

## 0.5.5 - 2020-10-12
- Fix qualified symbol auto-completion

## 0.5.4 - 2020-09-29
- Fix syntax definition errors for reify and let

## 0.5.3 - 2020-09-28
- Fix color scheme error on package update

## 0.5.2 - 2020-09-28
- Fix `<0x0d>` showing up in evaluation results on Windows
- Fix editing settings on Windows

## 0.5.1 - 2020-09-28
- Add a number of default key bindings

## 0.5.0 - 2020-09-27
- Initial alpha release
