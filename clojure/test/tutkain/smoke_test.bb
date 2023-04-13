(ns tutkain.smoke-test
  (:require [clojure.test :refer [deftest is]]
            [clojure.spec.alpha :as spec]
            [tutkain.rpc.test :refer [string->base64 send-op]]
            [tutkain.completions :as completions]
            [tutkain.completions.specs :as completions.specs]
            [tutkain.lookup :as lookup]
            [tutkain.query]
            [tutkain.test])
  (:import (java.time LocalDate)))

(deftest smoke
  ;; completions
  (is
    (spec/valid?
      (completions.specs/prefixed-candidates ::completions.specs/completions "m")
      (completions/candidates "m" 'user)))

  (is
    (spec/valid?
      (completions.specs/prefixed-candidates
        (spec/coll-of ::completions.specs/top-level-class-completion :min-count 1) "java.time")
      (completions/candidates "java.time" 'user)))

  (is
    (spec/valid?
      (completions.specs/prefixed-candidates
        (spec/coll-of ::completions.specs/top-level-class-completion :min-count 1) "LocalDate")
      (completions/candidates "LocalDate" 'tutkain.smoke-test)))

  ;; lookup
  (is (= {:name 'mapcat
          :arglists ["[f]" "[f & colls]"]
          :doc
          "Returns the result of applying concat to the result of applying map\n  to f and colls.  Thus function f should return a collection. Returns\n  a transducer when no collections are provided"
          :ns "clojure.core"}
        (lookup/lookup (find-ns 'clojure.core) "mapcat")))

  ;; test
  (is (= {:fail []
          :pass [{:type :pass :line 0 :var-meta {:file nil :line 1 :column 60 :name 'baz :ns "foo.bar"}}]
          :error []
          :tag :ret
          :val "{:test 1, :pass 1, :fail 0, :error 0, :assert 1, :type :summary}\n"}
        (send-op
          {:op :test
           :eval-lock (Object.)
           :ns "foo.bar"
           :code (string->base64 "(ns foo.bar (:require [clojure.test :refer [deftest is]])) (deftest baz (is (= 1 1)))")
           :vars ["baz"]})))


  ;; apropos
  (is (contains? (set (map #(select-keys % [:name :type :ns]) (:results (send-op {:op :apropos :pattern "reduce"}))))
        {:name 'areduce :type :macro :ns "clojure.core"}))

  ;; dir
  (is (contains? (set (:results (send-op {:op :dir :ns 'user :sym 'mapcat})))
        {:name 'mapcat
         :arglists ["[f]" "[f & colls]"]
         :doc "Returns the result of applying concat to the result of applying map\n  to f and colls.  Thus function f should return a collection. Returns\n  a transducer when no collections are provided"
         :type :function
         :ns "clojure.core"})))
