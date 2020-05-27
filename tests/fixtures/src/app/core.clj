(ns app.core
  (:require [clojure.set :as set]))

(defn square
  [x]
  (* x x))

(comment
  (+ 1 2)
  (range 512)
  (square 4)
  (set/union #{1 2 3} #{3 4 5})
  (println "Hello, world!")
  (def f (future (Thread/sleep 1000) (println "Hello, world!") (map inc (range 10))))
  (deref f)
  )
