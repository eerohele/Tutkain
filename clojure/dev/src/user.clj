(ns user
  (:require [cognitect.transcriptor :as xr]))

(defn run-tests
  []
  (run! xr/run (xr/repl-files "repl")))

(defn -main
  [& _]
  (run-tests)
  (shutdown-agents))

(comment
  (run-tests)
  )
