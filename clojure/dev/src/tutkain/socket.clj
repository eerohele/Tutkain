(ns tutkain.socket
  (:require [clojure.edn :as edn])
  (:import
   (clojure.lang LineNumberingPushbackReader EdnReader$ReaderException)
   (java.io BufferedReader BufferedWriter InputStreamReader OutputStreamWriter)
   (java.net Socket SocketTimeoutException)))

(defn client
  [& {:keys [host port timeout] :or {timeout 500}}]
  (let [socket (doto (Socket. host port) (.setSoTimeout timeout))
        reader (-> socket .getInputStream InputStreamReader. BufferedReader. LineNumberingPushbackReader.)
        writer (-> socket .getOutputStream OutputStreamWriter. BufferedWriter.)]
    {:reader reader
     :writer writer
     :send (fn [message]
             (.write writer (str (pr-str message) \newline))
             (.flush writer))
     :recv (fn []
             (try
               (edn/read {:eof ::EOF
                          :default tagged-literal
                          :readers {'error identity}} reader)
               (catch EdnReader$ReaderException ex
                 (if (= (type (ex-cause ex)) SocketTimeoutException)
                   ::timeout
                   (throw ex)))))
     :stop (fn []
             (.close reader)
             (.close writer)
             (.close socket))}))

