# Tutkain

A bare-bones [Clojure] nREPL client for [Sublime Text].

![image](https://user-images.githubusercontent.com/31859/77619123-353cf980-6f40-11ea-9bc8-4667a509489f.png)

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

| Command  | Binding |
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

## Background

I'm a happy [Cursive] user, but Intellij IDEA has a rather frustrating tendency
of grinding to a halt every now and then. That triggered this attempt at
turning Sublime Text into a somewhat viable Clojure editor.

Tutkain is very limited in scope. Its sole aim is the ability to interact
with a Clojure nREPL server. It is not, and never will be, a full-fledged
Clojure IDE. If you're looking for an IDE-like experience, consider
complementing Tutkain with these Sublime Text plugins:

- [paredit]
- [sublime-lispindent]
- [Sublime LSP](https://github.com/sublimelsp/LSP/blob/master/docs/index.md#clojurea-nameclojure)

Alternatively, use [Cursive], [Calva], [CIDER], or some other actual IDE.

## See also

- [Socket]

[Calva]: https://github.com/BetterThanTomorrow/calva
[CIDER]: https://github.com/clojure-emacs/cider
[clojure]: https://www.clojure.org
[Cursive]: https://cursive-ide.com
[Tutkain]: https://github.com/eerohele/tutkain
[Package Control]: https://www.packagecontrol.io
[paredit]: https://github.com/odyssomay/paredit
[Socket]: https://github.com/nasser/Socket
[sublime-lispindent]: https://github.com/odyssomay/sublime-lispindent
[Sublime Text]: https://www.sublimetext.com
