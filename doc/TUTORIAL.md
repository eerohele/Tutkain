# Tutorial

## Prerequisites

* [Clojure CLI tools](https://clojure.org/guides/getting_started#_clojure_installer_and_cli_tools) (the `clojure` command)

You can [use Tutkain with Leiningen](https://stackoverflow.com/a/34932745/825783), too. This tutorial presumes you can run `clojure`.

## Steps

1. On the command line, start a Clojure prepl server.

   I recommend [Propel]. If you've added a [`deps.edn` alias for Propel](https://clojure.org/reference/deps_and_cli#_aliases),
   to launch a prepl server, run:

   ```bash
   clojure -A:propel --write-port-file
   ```

2. In Sublime Text, open the command palette.

3. Run the **Tutkain: Connect** command.

   If you opened Sublime Text in the same folder where you started Propel,
   Tutkain attempts to auto-detect the port to connect to. Otherwise, enter
   the host and port when prompted. Propel prints the port it uses on startup.

3. Use the **Tutkain: Evaluate …** commands to send forms to the prepl server
   for evaluation.

   The **Tutkain: Evaluate Form** command works something like this:

   - If your cursor is at a left bracket, send the form it starts.
   - If your cursor is at a right bracket, send the form it closes.
   - Otherwise, send the form your cursor is inside.

If you accidentally close the Tutkain output panel, use the **Tutkain: Toggle
Output Panel** command to bring it up.

[Propel]: https://github.com/Olical/propel
