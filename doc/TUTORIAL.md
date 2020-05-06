# Tutorial

## Prerequisites

One of:

* [Clojure CLI tools](https://clojure.org/guides/getting_started#_clojure_installer_and_cli_tools) (the `clojure` command)
* [Leiningen](https://www.leiningen.org)

## Steps

1. On the command line, start a Clojure [nREPL] server.

   ```bash
   # With tools.deps (the `clojure` command):
   $ clojure -Sdeps '{:deps {nrepl {:mvn/version "0.7.0"}}}' --main nrepl.cmdline --port 1234

   # With Leiningen:
   $ lein repl :headless :port 1234
   ```

   See the [nREPL documentation](https://nrepl.org/nrepl/0.7.0/usage/server.html)
   for more information on starting an nREPL server.

2. In Sublime Text, open the command palette.

3. Run the **Tutkain: Connect** command.

   Enter the host (`localhost`) and port (`1234`) when prompted.

3. Use the **Tutkain: Evaluate …** commands to send forms to the nREPL server
   for evaluation.

   The **Tutkain: Evaluate Form** command works something like this:

   - If your cursor is at a left bracket, send the form it starts.
   - If your cursor is at a right bracket, send the form it closes.
   - Otherwise, send the form your cursor is inside.

If you accidentally close the Tutkain output panel, use the **Tutkain: Toggle
Output Panel** command to bring it up.

[nREPL]: https://nrepl.org
