(ns tutkain.tutorial)

;; Getting Started with Tutkain
;; ----------------------------
;;
;; Welcome! Tutkain is an interactive Clojure editing environment for Sublime Text. This tutorial
;; shows you how to get started with using Tutkain to edit Clojure.
;;
;; Editing Clojure is centered on what's called the "REPL", or the Read-Evaluate-Print Loop. In
;; short, that means _reading_ an independent unit of code (often called a "form"), _evaluating_ it,
;; _printing_ the result, and starting over.
;;
;; Tutkain handles the reading, printing, and looping, but it needs help with the evaluating. To
;; evaluate code, you need to connect Tutkain to an nREPL server. Tutkain sends the code you tell it
;; to read to the nREPL server. The nREPL server evaluates the code, returns the result to Tutkain,
;; which then prints it for you to see.
;;
;; Before you continue this tutorial, you must start an nREPL server. To do that, you can use one of
;; these tools:
;;
;; * Clojure CLI tools[^1]
;; * Leiningen (https://www.leiningen.org)
;;
;; NOTE: Many Tutkain features rely on nREPL 0.8 or newer. You can use Tutkain with older nREPL
;; versions, but features such as pretty-printing, documentation popups, and completion support
;; will not be available.
;;
;; Once you've installed one of them, open a terminal and start an nREPL server that listens on port
;; 1234 like this:
;;
;;   # Clojure CLI tools
;;   $ clojure -Sdeps '{:deps {nrepl {:mvn/version "0.8.0-alpha5"}}}' --main nrepl.cmdline --port 1234
;;
;;   # Leiningen
;;   $ lein repl :headless :port 1234
;;
;; If everything went OK, you'll see a message like this appear in the terminal:
;;
;;   nREPL server started on port 1234 on host localhost - nrepl://localhost:1234
;;
;; TIP: Tutkain looks for a file called .nrepl-port in your Sublime Text project root directory. If
;; it finds one, it suggests the port number it finds in that file when connecting to an nREPL
;; server. That means that if you start the nREPL server in a directory that is also a Sublime Text
;; project root directory, you do not need to specify the port number when starting the nREPL server
;; or when connecting to it.
;;
;; Now that you have an nREPL server running, you can start sending code from Tutkain to the nREPL
;; server for evaluation:
;;
;; 1. In Sublime Text, open the Command Palette (Tools > Command Palette).
;; 2. In the Command Palette, choose Tutkain: Connect.
;; 3. In the prompt that appears, press Enter to choose "localhost" as the host.
;; 4. In the next prompt, type the port number 1234 and press Enter.
;;
;; There should now be a new panel at the bottom of your Sublime Text window.
;; That means Tutkain is now connected to the nREPL server and you can start
;; evaluating code. Let's start with an easy example:
;;
;; 1. Move your cursor to the beginning of the next line of code:

(+ 1 2 3)

;; 2. Open the Command Palette and choose Tutkain: Evaluate Form.
;;
;;    This text should appear in the output panel:
;;
;;        tutkain.tutorial=> (+ 1 2 3)
;;        6
;;
;; Congratulations! You've taken your first small but significant step in
;; interactive editing.
;;
;; You don't want to go through the Command Palette every time to evaluate a
;; form, however. Let's assign a key binding to the Evaluate Form command to
;; make it easier to work with the REPL.
;;
;; Tutkain comes with (almost) no key bindings by default. However, it's
;; easy to define your own. To add a key binding for the Evaluate Form
;; command:
;;
;; 1. Open the Command Palette.
;; 2. Run the Tutkain: Edit Key Bindings command.
;;
;; You should see a set of example key binding definitions on the left, and your key binding
;; configuration file on the right. Scroll down the example key binding list a bit until you see
;; the key binding for the "tutkain_evaluate_form" command. Copy-paste it into your key binding
;; configuration file on the right and save it. Note the key combination for the command
;; (Control+C, followed by another Control+C).
;;
;; To make sure the key binding works, move your cursor anywhere on top of this form and press the
;; key combination.

(println "Hello, world!")

;; The text "Hello, world!" should appear in the output view.
;;
;; Tutkain aims to make it easy to evaluate forms. Here's a rundown of how Tutkain determines what
;; to evaluate:
;;
;; - If you have one or more selections, Tutkain evaluates the selections.
;; - If you're next to a bracket or some other character that delimits a top-level Clojure form (a
;;   form that is not surrounded by any other forms) Tutkain evaluates that form.
;; - Otherwise, if your cursor is somewhere inside a pair of brackets, Tutkain evaluates the
;;   outermost form your cursor is in.
;;
;; You can try this out yourself. Move your cursor anywhere on top of the following form and
;; evaluate it. You should get the same result every time. You can then select "(range 10)" and
;; evaluate it. You should get a different result.

(map inc (range 10))

;; An easy way to select forms for evaluation is to use the Tutkain: Expand Selection command. Try
;; it out on the form above:
;;
;; 1. Move your cursor to the point before "10" and evaluate.
;; 2. Via the Command Palette, run "Tutkain: Expand Selection" command.

;; * Clojure Language Server Protocol:
;;   https://github.com/snoe/clojure-lsp
;; * Sublime Language Server Protocol:
;;   https://github.com/sublimelsp/LSP/blob/master/docs/index.md#clojure
;; * Programming at the REPL:
;;   https://clojure.org/guides/repl/introduction

(comment
  (require '[clojure.java.browse :refer [browse-url]])

  ;; Evaluate the form to open the link in your default browser.
  (browse-url "https://clojure.org/guides/getting_started#_clojure_installer_and_cli_tools")
  (browse-url "https://www.leiningen.org"))
