(ns tutkain.analyzer.jvm-test
  (:require [clojure.test :refer [deftest are]]
            [tutkain.analyzer :as analyzer]
            [tutkain.analyzer.jvm :as jvm]
            [tutkain.rpc.test :refer [string->reader]]))

(defn ^:private points
  "Given a string, return a vector of all the line and column tuples in the string."
  [^String s]
  (let [len (.length s)]
    (loop [points [] index 0 line 1 column 1]
      (if (= index len)
        (conj points [line column])
        (case (.charAt s index)
          \newline
          (recur (conj points [line column]) (inc index) (inc line) 1)
          (recur (conj points [line column]) (inc index) line (inc column)))))))

(comment (points "a\nb") ,,,)

(defn ^:private local-symbols-at-points
  "Given a string, return a vector of [line column symbols] tuples."
  [s]
  (let [forms (analyzer/read-forms (string->reader s) jvm/reader-opts 1 1)
        nodes (jvm/analyze :local-symbols forms)]
    (mapv (fn [[line column]]
            [line column (analyzer/local-symbols line column nodes)])
      (points s))))

(comment (local-symbols-at-points "(let [x 1] (prn x) (let [y 2]) (+ x y))") ,,,)

(deftest local-symbols
  (are [ret s] (= ret (local-symbols-at-points s))
    ;; edge cases
    '[[1 1 ()] [1 2 ()] [1 3 ()]] "()"
    '[[1 1 ()] [1 2 ()]] "x"
    '[[1 1 ()] [1 2 ()] [1 3 ()] [1 4 ()] [1 5 ()] [2 1 ()] [2 2 ()] [2 3 ()] [2 4 ()] [2 5 ()]]
    "(inc\n  x)"

    ;; fn
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 (x)]
      [1 8 (x)]
      [1 9 ()]]
    "(fn [x])"

    ;; fn with newline
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 (x)]
      [1 8 (x)]
      [2 1 (x)]
      [2 2 (x)]
      [2 3 (x)]
      [2 4 (x)]
      [2 5 (x)]
      [2 6 (x)]
      [2 7 (x)]
      [2 8 (x)]
      [2 9 ()]]
    "(fn [x]\n(inc x))"

    ;; nested fn with newline
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 (x)]
      [1 8 (x)]
      [2 1 (x)]
      [2 2 (x)]
      [2 3 (x)]
      [2 4 (x)]
      [2 5 (x)]
      [2 6 (x)]
      [2 7 (x y)]
      [2 8 (x y)]
      [2 9 (x)]
      [2 10 ()]]
    "(fn [x]\n(fn [y]))"

    ;; let
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 (x)]
      [1 9 (x)]
      [1 10 (x)]
      [1 11 (x)]
      [1 12 ()]]
    "(let [x 1])"

    ;; let with newline
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 (x)]
      [1 9 (x)]
      [1 10 (x)]
      [1 11 (x)]
      [2 1 (x)]
      [2 2 (x)]
      [2 3 (x)]
      [2 4 (x)]
      [2 5 (x)]
      [2 6 (x)]
      [2 7 (x)]
      [2 8 (x)]
      [2 9 ()]]
    "(let [x 1]\n(inc x))"

    ;; let with multiple bindings
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 (x)]
      [1 9 (x)]
      [1 10 (x)]
      [1 11 (x)]
      [1 12 (x y)]
      [1 13 (x y)]
      [1 14 (x y)]
      [1 15 (x y)]
      [1 16 (x y)]
      [1 17 (x y)]
      [1 18 (x y)]
      [1 19 (x y)]
      [1 20 (x y)]
      [1 21 (x y)]
      [1 22 (x y)]
      [1 23 (x y)]
      [1 24 ()]]
    "(let [x 1 y 2] (+ x y))"

    ;; let with seq destructuring
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 (a)]
      [1 10 (a)]
      [1 11 (a b)]
      [1 12 (a b)]
      [1 13 (a b)]
      [1 14 (a b)]
      [1 15 (a b)]
      [1 16 (a b)]
      [1 17 (a b)]
      [1 18 (a b)]
      [1 19 (a b)]
      [1 20 ()]]
    "(let [[a b] [1 2]])"

    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 ()]
      [1 12 ()]
      [1 13 ()]
      [1 14 ()]
      [1 15 ()]
      [1 16 (a)]
      [1 17 (a)]
      [1 18 (a b)]
      [1 19 (a b)]
      [1 20 (a b)]
      [1 21 (a b)]
      [1 22 (a b)]
      [1 23 (a b)]
      [1 24 (a b)]
      [1 25 (a b)]
      [1 26 (a b)]
      [1 27 (a b)]
      [1 28 (a b)]
      [1 29 (a b)]
      [1 30 ()]]
    "(let [{:keys [a b]} {:a :b}])"

    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 (a)]
      [1 10 (a)]
      [1 11 (a)]
      [1 12 (a)]
      [1 13 (a)]
      [1 14 (a b)]
      [1 15 (a b)]
      [1 16 (a b)]
      [1 17 (a b)]
      [1 18 (a b)]
      [1 19 (a b)]
      [1 20 (a b)]
      [1 21 (a b)]
      [1 22 (a b)]
      [1 23 (a b)]
      [1 24 (a b)]
      [1 25 (a b)]
      [1 26 (a b)]
      [1 27 (a b)]
      [1 28 ()]]
    "(let [{a :a b :b} {:a :b}])"

    ;; with-open
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 ()]
      [1 12 ()]
      [1 13 ()]
      [1 14 (x)]
      [1 15 (x)]
      [1 16 (x)]
      [1 17 (x)]
      [1 18 ()]]
    "(with-open [x y])"

    ;; when-let
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 ()]
      [1 12 ()]
      [1 13 (x)]
      [1 14 (x)]
      [1 15 (x)]
      [1 16 (x)]
      [1 17 (x)]
      [1 18 (x)]
      [1 19 (x)]
      [1 20 ()]]
    "(when-let [x true])"

    ;; if-let
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 (x)]
      [1 12 (x)]
      [1 13 (x)]
      [1 14 (x)]
      [1 15 (x)]
      [1 16 (x)]
      [1 17 (x)]
      [1 18 (x)]
      [1 19 (x)]
      [1 20 (x)]
      [1 21 (x)]
      [1 22 (x)]
      [1 23 (x)]
      [1 24 ()]]
    "(if-let [x true] :t :f)"

    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 ()]
      [1 12 ()]
      [1 13 (x)]
      [1 14 (x)]
      [1 15 (x)]
      [1 16 (x)]
      [1 17 (x)]
      [1 18 (x)]
      [1 19 (x)]
      [1 20 (x)]
      [1 21 (x)]
      [1 22 (x)]
      [1 23 ()]]
    "(when-let [x true] :t)"

    ;; defmacro
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 (&form &env)]
      [1 12 (&form &env)]
      [1 13 (&form &env)]
      [1 14 (&form &env)]
      [1 15 (&form &env x)]
      [1 16 (&form &env x)]
      [2 1 (&form &env x)]
      [2 2 (&form &env x)]
      [2 3 (&form &env x)]
      [2 4 (&form &env x)]
      [2 5 (&form &env x)]
      [2 6 (&form &env x)]
      [2 7 (&form &env x)]
      [2 8 (&form &env x)]
      [2 9 (&form &env x)]
      [2 10 (&form &env x)]
      [2 11 ()]]
    "(defmacro m [x]\n`(inc ~x))"

    ;; defn
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 (x)]
      [1 12 (x)]
      [1 13 ()]]
    "(defn f [x])"

    ;; defn with nested let
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 (x)]
      [1 12 (x)]
      [2 1 (x)]
      [2 2 (x)]
      [2 3 (x)]
      [2 4 (x)]
      [2 5 (x)]
      [2 6 (x)]
      [2 7 (x)]
      [2 8 (x)]
      [2 9 (x)]
      [2 10 (x y)]
      [2 11 (x y)]
      [2 12 (x y)]
      [2 13 (x y)]
      [2 14 (x y z)]
      [2 15 (x y z)]
      [2 16 (x y z)]
      [2 17 (x y z)]
      [3 1 (x y z)]
      [3 2 (x y z)]
      [3 3 (x y z)]
      [3 4 (x y z)]
      [3 5 (x y z)]
      [3 6 (x y z)]
      [3 7 (x y z)]
      [3 8 (x y z)]
      [3 9 (x y z)]
      [3 10 (x y z)]
      [3 11 (x y z)]
      [3 12 (x y z)]
      [3 13 (x)]
      [3 14 ()]]
    "(defn f [x]\n  (let [y 1 z 2]\n    (+ x y)))"

    ;; defmethod
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 ()]
      [1 10 ()]
      [1 11 ()]
      [1 12 ()]
      [1 13 ()]
      [1 14 ()]
      [1 15 ()]
      [1 16 ()]
      [1 17 ()]
      [1 18 ()]
      [1 19 ()]
      [1 20 ()]
      [1 21 ()]
      [1 22 ()]
      [1 23 ()]
      [1 24 ()]
      [1 25 ()]
      [1 26 ()]
      [1 27 ()]
      [1 28 ()]
      [1 29 ()]
      [1 30 ()]
      [1 31 ()]
      [1 32 ()]
      [1 33 ()]
      [1 34 ()]
      [1 35 ()]
      [1 36 (x)]
      [1 37 (x)]
      [1 38 (x)]
      [1 39 (x)]
      [1 40 (x)]
      [1 41 (x)]
      [1 42 (x)]
      [1 43 (x writer)]
      [1 44 (x writer)]
      [1 45 (x writer)]
      [1 46 (x writer)]
      [1 47 ()]]
    "(defmethod print-method :unknown [x writer] x)"

    ;; loop
    '[[1 1 ()]
      [1 2 ()]
      [1 3 ()]
      [1 4 ()]
      [1 5 ()]
      [1 6 ()]
      [1 7 ()]
      [1 8 ()]
      [1 9 (x)]
      [1 10 (x)]
      [1 11 (x)]
      [1 12 (x)]
      [1 13 (x)]
      [1 14 (x)]
      [1 15 (x)]
      [1 16 (x)]
      [1 17 (x)]
      [1 18 (x)]
      [1 19 (x)]
      [1 20 (x)]
      [1 21 (x)]
      [1 22 (x)]
      [1 23 (x)]
      [1 24 (x)]
      [1 25 (x)]
      [1 26 (x)]
      [1 27 (x)]
      [1 28 (x)]
      [1 29 ()]]
    "(loop [x 1] (recur (inc x)))"))

(comment (local-symbols-at-points "(fn [x])") ,,,)
