(ns app.core-test
  (:require [clojure.test :refer [deftest is]]
            [app.test-util :as test-util]))

(deftest ok
  (is (= 2 (+ 1 1))))

(deftest nok
  (is (= 3 (+ 1 1)))
  (is (empty? [1])))

(deftest error
  (is (= {:a 1} {:a 2}))
  (is (= 4 (+ 2 2)))
  (is (= 0 (/ 4 0)))
  (is (= {:a 2} (update {:a 1} :a inc))))

(deftest util
  (is (= 1 (test-util/my-util-fn 1))))
