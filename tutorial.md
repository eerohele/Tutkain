# Getting Started with Tutkain

Welcome! Tutkain is an interactive Clojure development environment. This
tutorial shows you how to get started using Tutkain to develop Clojure
programs.

To use Tutkain, you must connect it to a Clojure runtime. To do that, you
must launch a Clojure socket server.

## Starting and connecting to a Clojure runtime

To launch a Clojure socket server:

1. Install the [Clojure command-line tools](https://clojure.org/guides/getting_started).
2. To launch a socket server that listens on port 1234, on the command line, run:

   ```bash
   clojure -J-Dclojure.server.repl="{:port 1234 :accept clojure.core.server/repl}"
   ```

To connect Tutkain to the socket server:

1. In Sublime Text, open the Command Palette (**Tools** » **Command Palette**).
2. Choose **Tutkain: Connect**.
3. Choose **Clojure**.
4. Press Enter to choose `localhost`.
5. Type 1234 and press Enter.

Tutkain opens an output panel at the bottom of your Sublime Text window and prints the Clojure version of the runtime you're connected to.

You are now connected to the Clojure runtime listening on `localhost:1234`. That means you are ready evaluate code.

## A note on key bindings

To avoid inevitable key binding conflicts, Tutkain comes with no key bindings
enabled by default.

This tutorial proposes a few key bindings. You don't need to add any right now.

If you want, though, you can explore some of the available key bindings:

1. Open the Command Palette.
2. Choose **Tutkain: Edit Key Bindings**.

## Evaluating code

* * *
This tutorial is a [Markdown](https://daringfireball.net/projects/markdown/syntax) file. Normally, you'll evaluate code from within a Clojure file. With Tutkain, you can also evaluate code in Clojure code blocks in Markdown documents.
* * *

To send a Clojure code from Tutkain to the Clojure runtime for evaluation:

1. Move your caret anywhere on top of the Clojure code below (on the line between the two lines with backticks).

   ```clojure
   (+ 1 2 3)
   ```

2. Open the Command Palette and choose **Tutkain: Evaluate** » **Outermost
S-expression**.

In the output panel, Tutkain prints the code you evaluated and the evaluation
result (the number `6`).

To hide the output panel, press the Escape key. Tutkain shows the output panel
every time you evaluate code.

## Using a key binding to evaluate code

Instead of using the Command Palette every time to evaluate code, you'll want to use a key binding.

To configure Tutkain to use the Alt key followed by the Enter key to evaluate
code:

1. Open the Command Palette and choose **Tutkain:: Edit Key Bindings**.
2. In the window that appears, into the right-hand pane, inside the square brackets (`[]`), copy-paste this key binding configuration (the text between the lines with the backticks):

   ```json
   {
     "keys": ["alt+enter"],
     "command": "tutkain_evaluate",
     "args": {
       "scope": "outermost",
       "ignore": ["comment"]
     },
     "context": [{
       "key": "selector",
       "operator": "equal",
       "operand": " source.clojure"
     }]
   },
   ```

3. Close the key binding window.

To evaluate code using the key binding:

1. Move your caret anywhere on top of the Clojure code below.

   ```clojure
   (+ 1 2 3)
   ```

2. Press Alt and Enter at the same time.

Tutkain prints the evaluation input and output in the output panel.

## Using evaluation scopes

With Tutkain, you can evaluate code at a number of different scopes. For example, instead of the outermost S-expression, you can evaluate the innermost S-expression.

This tutorial only shows a few of the available evaluation scopes. For information on all available scopes, evaluate the form in the code block below:

```clojure
(clojure.java.browse/browse-url
  "https://tutkain.flowthing.me/#evaluating-code")
```

### Evaluating a form or view up to a point

When working with threading macros (for example, `->` or `->>`), instead of evaluating the entire form, it can be useful to evaluate code only up to the current caret position.

To evaluate a form up to a point:

1. Move your caret such that it immediately follows `(* 42)` in the Clojure
   code below.

   ```clojure
   (-> 1 inc (* 42) (/ 4))
   ```

2. Open the Command Palette and choose **Tutkain: Evaluate** » **Up to Point**.

Instead of evaluating the entire form, Tutkain evaluates `(-> 1 inc (* 42)`.

Evaluating up to a point is also useful when you want to evaluate top-level forms up to a point.

For example, given:

```clojure
(def a (atom 1))
(swap! a inc)
(swap! a (partial * 42))
(swap! a (partial / 4))
```

If you move your caret such that it immediately follows `(swap! a (partial * 42))`, Tutkain evaluates that form and every top-level form that precedes it.

As with other evaluation scopes, you probably want to configure a key binding (via **Tutkain: Edit Key Bindings**) to evaluate code up to a point.

## Using comment forms

By default, when you evaluate the outermost S-expression, Tutkain disregards
the `comment` form when looking for the outermost S-expression to evaluate.
This makes it easy to use `comment` forms to work on one function or macro
at a time.

To use `comment` forms:

1. In the Clojure code block below, put your caret anywhere inside the `defn square` form.

   ```clojure
   (defn square
     [x]
     (* x x))

   (comment
     (square "a")
     (square 2)
     ,,,)
   ```

2. Hit Alt+Enter to evaluate the form and create the `square` function.
3. Move your caret on the first `square` form inside the `comment` form.
4. Hit Alt+Enter to evaluate it.

   Instead of evaluating the `comment` form, which is the outermost
   S-expression, Tutkain evaluates the `square` form.

   Since `square` does not work with a string argument, in the output panel,
   Tutkain shows you an error highlighted in red.

5. Move your caret on the second `square` form inside the `comment` form.
6. Hit Alt+Enter to evaluate it.

   In the output panel, Tutkain shows you the evaluation input and output.

## Looking up var metadata

Tutkain uses the information in the Clojure runtime to show you information about the vars in the runtime.

To look up documentation and other var metadata:

1. Move your caret on of `map` (or any other symbol) in the Clojure code below.

   ```clojure
   (map inc (range 10))
   ```

2. Open the Command Palette and choose **Tutkain » Show Information**.

Tutkain shows the fully qualified name of the function, all its argument lists,
and its docstring.

You can also tell Tutkain to look up var metadata when you hover your mouse
cursor over a symbol:

1. **Preferences** » **Package Settings** » **Tutkain**.
2. In the right-hand pane, inside the top-level curly braces (`{}`), add:

   ```json
   "lookup_on_hover": true,
   ```

## Using goto definition

Tutkain uses the information in the Clojure runtime to take you to the definition of vars.

To go to the definition a var:

1. Move your caret on of `map` (or any other symbol) in the Clojure code below.

   ```clojure
   (map inc (range 10))
   ```

2. Open the Command Palette and choose **Tutkain: Goto Definition**.

* * *
If you come across a symbol for which **Tutkain: Goto Definition** doesn't
seem to work, the var the symbol names probably hasn't been loaded into the runtime. Try to `require` the namespace that contains the var and try again.
* * *

## Using auto-completion

Tutkain uses the information in the Clojure runtime to auto-complete symbols, keywords, Java class names, and other things.

To try some of Tutkain's auto-completion features, follow the prompts in the Clojure code block below.

```clojure
;; Below this line, type clojure.repl/

;; Below this line, type :clojure.core/

;; Below this line, type java.time.

```

## Embracing the runtime

Tutkain uses the information available in the runtime -- not static analysis
-- to get var metadata. This means Tutkain supports looking up metadata and goto definition for things like `printer` in the (admittedly contrived) example below.

```clojure
(defmacro defun
  [name docstring]
  `(defn ~name {:doc ~docstring :arglists '([~'argument])}
     [arg#]
     (println arg#)))

(defun printer "Prints its sole argument.")

(printer "Hello, world!")
```

Doing the same with static analysis would be exceedingly difficult.

<!--
The most important part of Tutkain is the REPL. The REPL — the Read-
Evaluate-Print Loop — is the most important tool for writing Clojure
programs. The REPL is a program that *reads* an independent unit of code
(often called a "form"), *evaluates* it, *prints* the result, and starts
over (*loops*).

Tutkain takes care of the reading, printing, and looping for you. All you
need to do is the evaluating. To evaluate code, you need to connect Tutkain
to a Clojure runtime. Then, Tutkain sends the code you tell it the runtime
The nREPL server evaluates the code, returns the result to Tutkain, which
then prints it for you to see.

Before you continue this tutorial, you must start an nREPL server. To do
that, you can use one of these tools:

* Clojure CLI tools[^1] * Leiningen (https://www.leiningen.org)

NOTE: Many Tutkain features rely on nREPL 0.8 or newer. You can use Tutkain
with older nREPL versions, but features such as pretty-printing,
documentation popups, and completion support will not be available.

Once you've installed one of them, open a terminal and start an nREPL server
that listens on port 1234 like this:

# Clojure CLI tools $ clojure -Sdeps '{:deps {nrepl {:mvn/version
"0.8.0-alpha5"}}}' --main nrepl.cmdline --port 1234

# Leiningen $ lein repl :headless :port 1234

If everything went OK, you'll see a message like this appear in the
terminal:

nREPL server started on port 1234 on host localhost - nrepl://localhost:1234

TIP: Tutkain looks for a file called .nrepl-port in your Sublime Text
project root directory. If it finds one, it suggests the port number it
finds in that file when connecting to an nREPL server. That means that if
you start the nREPL server in a directory that is also a Sublime Text
project root directory, you do not need to specify the port number when
starting the nREPL server or when connecting to it.

Now that you have an nREPL server running, you can start sending code from
Tutkain to the nREPL server for evaluation:

1. In Sublime Text, open the Command Palette (Tools > Command Palette). 2.
In the Command Palette, choose Tutkain: Connect. 3. In the prompt that
appears, press Enter to choose "localhost" as the host. 4. In the next
prompt, type the port number 1234 and press Enter.

There should now be a new panel at the bottom of your Sublime Text window.
That means Tutkain is now connected to the nREPL server and you can start
evaluating code. Let's start with an easy example:

1. Move your cursor to the beginning of the next line of code:

(+ 1 2 3)

2. Open the Command Palette and choose Tutkain: Evaluate Form.

   This text should appear in the output panel:

       tutkain.tutorial=> (+ 1 2 3)
       6

Congratulations! You've taken your first small but significant step in
interactive editing.

You don't want to go through the Command Palette every time to evaluate a
form, however. Let's assign a key binding to the Evaluate Form command to
make it easier to work with the REPL.

Tutkain comes with (almost) no key bindings by default. However, it's
easy to define your own. To add a key binding for the Evaluate Form
command:

1. Open the Command Palette.
2. Run the Tutkain: Edit Key Bindings command.

You should see a set of example key binding definitions on the left, and your key binding
configuration file on the right. Scroll down the example key binding list a bit until you see
the key binding for the "tutkain_evaluate_form" command. Copy-paste it into your key binding
configuration file on the right and save it. Note the key combination for the command
(Control+C, followed by another Control+C).

To make sure the key binding works, move your cursor anywhere on top of this form and press the
key combination.

(println "Hello, world!")

The text "Hello, world!" should appear in the output view.

Tutkain aims to make it easy to evaluate forms. Here's a rundown of how Tutkain determines what
to evaluate:

- If you have one or more selections, Tutkain evaluates the selections.
- If you're next to a bracket or some other character that delimits a top-level Clojure form (a
  form that is not surrounded by any other forms) Tutkain evaluates that form.
- Otherwise, if your cursor is somewhere inside a pair of brackets, Tutkain evaluates the
  outermost form your cursor is in.

You can try this out yourself. Move your cursor anywhere on top of the following form and
evaluate it. You should get the same result every time. You can then select "(range 10)" and
evaluate it. You should get a different result.

(map inc (range 10))

An easy way to select forms for evaluation is to use the Tutkain: Expand Selection command. Try
it out on the form above:

1. Move your cursor to the point before "10" and evaluate.
2. Via the Command Palette, run "Tutkain: Expand Selection" command.

* Clojure Language Server Protocol:
  https://github.com/snoe/clojure-lsp
* Sublime Language Server Protocol:
  https://github.com/sublimelsp/LSP/blob/master/docs/index.md#clojure
* Programming at the REPL:
  https://clojure.org/guides/repl/introduction

(comment
  (require '[clojure.java.browse :refer [browse-url]])

  Evaluate the form to open the link in your default browser.
  (browse-url "https://clojure.org/guides/getting_started#_clojure_installer_and_cli_tools")
  (browse-url "https://www.leiningen.org"))


To


- add alt+enter key binding for eval
- suggest key binding for documentation popup
- suggest key binding for goto definition
  - mention that goto definition supports things static tools can never support
-->
