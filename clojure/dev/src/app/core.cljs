(ns app.core)

(defn parse-int
  [x]
  (js/parseInt x 10))

(comment
  (require '[cljs.repl :as repl])
  (require '[cljs.repl.node :as node])
  (repl/repl (node/repl-env) :need-prompt (constantly false))
  )
