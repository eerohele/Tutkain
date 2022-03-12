(ns user
  (:require
   [cognitect.transcriptor :as xr]))

(defn run-tests
  []
  (run! xr/run (xr/repl-files "repl")))

(defn -main
  [& _]
  (run-tests)
  (shutdown-agents))

(comment
  (run-tests)
  ,,,)

(comment
  (require
    '[clojure.repl :as repl]
    '[tutkain.analyzer :refer [local-positions]]
    '[tutkain.completions :refer [candidates]]
    '[criterium.core :refer [quick-bench]])

  (quick-bench (candidates "java." 'clojure.core))

  (quick-bench
    (local-positions
      {:file "clojure/core.clj"
       :ns (the-ns 'clojure.core)
       :context (with-out-str (repl/source clojure.core/doseq))
       :form 'seq-exprs
       :start-line 0
       :start-column 0
       :line 5
       :column 4
       :end-column 13}))
  )
