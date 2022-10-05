(ns bb-test
  (:require [clojure.test :refer [deftest is]]))

(deftest ok
  (is (= 2 (+ 1 1))))

(deftest nok
  (is (= 3 (+ 1 1)))
  (is (empty? [1])))

(deftest error
  (is (= {:a 1} {:a 2}))
  (is (= 0 (/ 4 0)))
  (is (= {:a 2} (update {:a 1} :a inc))))
