(ns tutkain.nrepl.util.pprint
  (:require
   [clojure.datafy :refer [datafy]]
   [tutkain.fipp.v0v6v23.fipp.edn :as fipp]))

(defn pprint
  [value writer options]
  (fipp/pprint
    (if (instance? Throwable value) (datafy value) value)
    (assoc options :writer writer)))
