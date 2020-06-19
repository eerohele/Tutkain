(ns app.core)

(defn parse-int
  [x]
  (js/parseInt x 10))

(comment
  ; Evaluate these before evaluating the view.
  (require 'cider.piggieback)
  (require '[cljs.repl.node])
  (cider.piggieback/cljs-repl (cljs.repl.node/repl-env))

  (parse-int "42")
  )
