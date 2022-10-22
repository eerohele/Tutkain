(ns tutkain.format
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint]))

(defn Throwable->str
  "Print a java.lang.Throwable into a string."
  [t]
  #?(:bb (with-out-str (repl/pst t))
     :clj (-> t Throwable->map main/ex-triage main/ex-str)))

(defn pp-str
  [x]
  (binding [pprint/*print-right-margin* 100]
    (-> x pprint/pprint with-out-str)))


