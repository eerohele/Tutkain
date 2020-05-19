(ns core.test
  (:require [clojure.test :refer [deftest is]]))

(deftest ok
  (is (= 2 (+ 1 1))))

(deftest nok
  (is (= 3 (+ 1 1))))
