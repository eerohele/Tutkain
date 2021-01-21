(ns app.core
  (:require [clojure.set :as set]
            [app.other :as other]))

(defn square
  [x]
  (* x x))

(defn foo
  [a b]
  (* (other/sum a b) (other/sum a b)))

(comment
  (+ 1 2)
  (throw (ex-info "Boom!" {:a :1}))
  (range 512)
  (square 4)
  (foo 3 4)
  (tap> (rand-int 42))
  (set/union #{1 2 3} #{3 4 5})
  (println "Hello, world!")
  (def f (future (Thread/sleep 1000) (println "Hello, world!") (map inc (range 10))))
  (deref f)

  (into (sorted-map)
    (zipmap (map (comp keyword str char) (range 97 123))
      (range 1 26)))
  )
