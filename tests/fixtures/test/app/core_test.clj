(ns core.test
  (:require [clojure.test :refer [deftest is]]))

(defn square
  [x]
  (* x x))

(square 2)

(deftest ok
  (is (= 3 (+ 1 1))))

(deftest nok
  (is (= 3 (+ 1 1))))
