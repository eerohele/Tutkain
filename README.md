# Tutkain

A bare-bones [Clojure] nREPL client for [Sublime Text].

![image](https://user-images.githubusercontent.com/31859/81447151-c7156480-9184-11ea-91a1-2b6de66c2bbe.png)

## Status

**Currently unreleased**.

**Alpha**. Expect breaking changes and a veritable cavalcade of bugs.

## Install

1. Clone this repository into your Sublime Text `Packages` directory.
   (Installation via Package Control coming up.)

## Help

* [Tutorial](doc/TUTORIAL.md)

## Goals

- Simple
- Fast
- Easy to hack on
- Few code dependencies (currently zero)

## Non-goals

- Full IDE experience (can leverage [Sublime LSP] and [clojure-lsp] for static
  analysis, though — maybe write a tutorial?)

## Maybe-goals

- Reimplement [paredit] with better Clojure support

## Key bindings

None, because any default key binding set I introduce would cause conflicts
anyway. I'll supply sample key binding sets instead and try to make it as easy
as possible to take them into use. TBA.

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
