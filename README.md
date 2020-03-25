# Tutkain

A bare-bones [Clojure] [socket REPL] client for [Sublime Text].

## Status

**Currently unreleased**.

**Alpha**. Expect breaking changes.

## Install

1. Via [Package Control], install [paredit].
1. Clone this repository into your Sublime Text `Packages` directory.
   (Installation via Package Control coming up.)

I wanted to steal parts of the [paredit] plugin into Tutkain, but
[it has no license](https://github.com/odyssomay/paredit/issues/29), so I
couldn't. Therefore, Tutkain currently has a hard dependency on paredit.

You almost definitely also want to install [sublime-lispindent] if you haven't
already.

## Help

* [Tutorial](doc/tutorial.md)

## Default key bindings

### macOS

<dl>
  <dt>Connect to Socket REPL<dt>
  <dd><kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>C</kbd></dd>
  <dt>Evaluate Form<dt>
  <dd><kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>F</kbd></dd>
  <dt>Evaluate View<dt>
  <dd><kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>V</kbd></dd>
  <dt>Disconnect from Socket REPL<dt>
  <dd><kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>D</kbd></dd>
  <dt>Show Output Panel<dt>
  <dd><kbd>⌘</kbd> + <kbd>R</kbd>, <kbd>⌘</kbd> + <kbd>O</kbd></dd>
</dl>

### Windows & Linux

None yet. Contributions welcome.

## Background

I'm a happy [Cursive] user, but Intellij IDEA has a rather frustrating tendency
of grinding to a halt every now and then. That triggered this attempt at
turning Sublime Text into a somewhat viable Clojure editor.

Tutkain is very limited in scope. Its sole aim is the ability to interact
with a Clojure socket REPL. It is not, and never will be, a full-fledged Clojure
IDE. If you're looking for an IDE-like experience, consider complementing
Tutkain with these Sublime Text plugins:

- [paredit]
- [sublime-lispindent]
- [Sublime LSP](https://github.com/sublimelsp/LSP/blob/master/docs/index.md#clojurea-nameclojure)

[clojure]: https://www.clojure.org
[Cursive]: https://cursive-ide.com
[Tutkain]: https://github.com/eerohele/tutkain
[Package Control]: https://www.packagecontrol.io
[paredit]: https://github.com/odyssomay/paredit
[socket REPL]: https://clojure.org/reference/repl_and_main
[sublime-lispindent]: https://github.com/odyssomay/sublime-lispindent
[Sublime Text]: https://www.sublimetext.com
