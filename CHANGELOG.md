# Changelog
All notable changes to this project will be documented in this file.

## Unreleased
- Add support for keyword auto-completion

  Requires nREPL 0.8.4 or newer, which has not yet been released at the time of this release.

- Improve documentation popup
- Improve sideloader error tolerance

  This allows Tutkain to connect to nREPL servers that run in environments where the nREPL sideloader cannot write temporary files.

## 0.6.0
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
