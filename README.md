# Tutkain

A bare-bones [Clojure] nREPL client for [Sublime Text].

![image](https://user-images.githubusercontent.com/31859/81447151-c7156480-9184-11ea-91a1-2b6de66c2bbe.png)

## Status

**Currently unreleased**.

**Alpha**. Expect breaking changes and a cavalcade of bugs.

## Install

1. Clone this repository into your Sublime Text `Packages` directory.
   (Installation via Package Control coming up.)

## Help

* [Tutorial](doc/TUTORIAL.md)

## Default key bindings

### macOS

| Command | Binding |
| ------------- | ------------- |
| Connect | <kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>C</kbd> |
| Evaluate Form | <kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>F</kbd> |
| Evaluate View | <kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>V</kbd> |
| Evaluate Input | <kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>I</kbd> |
| Disconnect | <kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>D</kbd> |
| Show Output Panel | <kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>O</kbd> |
| Clear Output Panel | <kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>X</kbd> |

### Windows & Linux

None yet. Contributions welcome.

## Design

Tutkain is very simple by design. It is narrowly focused on interacting with
[nREPL] servers.

For a fuller Clojure editing experience on Sublime Text, consider complementing
Tutkain with these Sublime Text plugins:

- [paredit]
- [sublime-lispindent]
- [Sublime LSP](https://github.com/sublimelsp/LSP/blob/master/docs/index.md#clojurea-nameclojure) with [clojure-lsp]

[clojure]: https://www.clojure.org
[clojure-lsp]: https://github.com/snoe/clojure-lsp
[nREPL]: https://nrepl.org
[Package Control]: https://www.packagecontrol.io
[paredit]: https://github.com/odyssomay/paredit
[sublime-lispindent]: https://github.com/odyssomay/sublime-lispindent
[Sublime LSP]: https://github.com/sublimelsp/LSP/blob/master/docs/index.md#clojurea-nameclojure
[Sublime Text]: https://www.sublimetext.com
