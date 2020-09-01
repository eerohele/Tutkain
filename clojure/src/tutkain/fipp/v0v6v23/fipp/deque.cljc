(ns tutkain.fipp.v0v6v23.fipp.deque
  "Double-sided queue built on rrb vectors."
  (:refer-clojure :exclude [empty concat])
  (:require [tutkain.corerrb-vector.v0v1v1.clojure.core.rrb-vector :as rrb]))

(def create vector)

(def empty [])

(defn popl [v]
  (subvec v 1))

(def conjr (fnil conj empty))

(defn conjlr [l deque r]
  (rrb/catvec [l] deque [r]))

(def concat rrb/catvec)
