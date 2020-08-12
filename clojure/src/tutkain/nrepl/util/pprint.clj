(ns tutkain.nrepl.util.pprint
  (:require
   [clojure.datafy :refer [datafy]]
   [fipp.edn :as fipp]))

(defn pprint
  [value writer options]
  (binding [*out* writer]
    (fipp/pprint (if (instance? Throwable value) (datafy value) value) options)))
