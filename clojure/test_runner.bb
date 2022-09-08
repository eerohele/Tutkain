#!/usr/bin/env bb

(require '[clojure.test :as t])

(def tests
  ['tutkain.smoke-test])

(apply require tests)

(def failures-and-errors
  (let [{:keys [fail error]} (apply t/run-tests tests)]
    (+ fail error)))

(System/exit failures-and-errors)
