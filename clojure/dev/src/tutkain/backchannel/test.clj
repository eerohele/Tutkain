(ns tutkain.backchannel.test
  "Utilities for testing Tutkain's backchannel ops."
  (:require
   [clojure.edn :as edn]
   [tutkain.backchannel :as backchannel])
  (:import
   (clojure.lang LineNumberingPushbackReader)
   (java.io StringReader)
   (java.util Base64)))

(defn send-op
  "Given a backchannel op, call the handler function on it and return the EDN
  response."
  [op]
  (->
    (assoc op :out-fn prn)
    backchannel/handle
    with-out-str
    edn/read-string))

(defn string->reader
  "Given a string, return a LineNumberingPushbackReader on the string."
  [string]
  (-> string StringReader. LineNumberingPushbackReader.))

(def ^:private encoder (Base64/getEncoder))

(defn string->base64
  "Encode a string as Base64."
  [string]
  (.encodeToString encoder (.getBytes string)))
