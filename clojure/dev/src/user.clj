(ns user
  (:require [cognitect.transcriptor :as xr]))

(defn run-tests
  [& _]
  (run! xr/run (xr/repl-files "repl")))

(comment
  (run-tests)
  )
