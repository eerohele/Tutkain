(ns tutkain.format
  (:require
   [clojure.main :as main]
   [tutkain.pprint :as pprint]))

(defn Throwable->str
  "Print a java.lang.Throwable into a string."
  [t]
  #?(:bb (with-out-str (clojure.repl/pst t))
     :clj (-> t Throwable->map main/ex-triage main/ex-str)))

(defn pp-str
  [x]
  (with-out-str (pprint/pprint x {:max-width 100})))
