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
  (require '[tutkain.completions :refer [candidates]])
  (require '[criterium.core :refer [quick-bench]])

  (quick-bench (candidates "java." 'clojure.core))
  ,,,)
