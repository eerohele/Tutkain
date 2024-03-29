(ns tutkain.clojuredocs
  (:require [clojure.edn :as edn]
            [clojure.java.io :as io]
            [tutkain.rpc :as rpc :refer [handle respond-to]])
  (:import (java.io PushbackReader)))

(defmethod handle :examples
  [{:keys [source-path sym] :as message}]
  (respond-to message
    (if-some [qualified-symbol (some-> (ns-resolve (rpc/namespace message) sym) symbol)]
      (with-open [reader (PushbackReader. (io/reader source-path))]
        (assoc (-> reader edn/read qualified-symbol) :symbol qualified-symbol))
      {:symbol sym})))
