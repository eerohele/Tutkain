(ns tutkain.base64
  (:require
   [tutkain.backchannel :refer [handle respond-to]]
   [tutkain.format :refer [Throwable->str]])
  (:import
   (clojure.lang LineNumberingPushbackReader)
   (java.io ByteArrayInputStream InputStreamReader FileNotFoundException)
   (java.util Base64)))

(def base64-decoder
  (Base64/getDecoder))

(defn base64-reader
  ^LineNumberingPushbackReader [blob]
  (->
    base64-decoder
    (.decode blob)
    (ByteArrayInputStream.)
    (InputStreamReader.)
    (LineNumberingPushbackReader.)))

(defn read-base64
  [blob path filename]
  #?(:bb (binding [*file* path]
           (load-string (String. (.decode base64-decoder blob) "UTF-8")))
     :clj (with-open [reader (base64-reader blob)]
            (Compiler/load reader path filename))))

(defmethod handle :load-base64
  [{:keys [blob path filename requires] :as message}]
  (try
    (some->> requires (run! require))
    (try
      (read-base64 blob path filename)
      (respond-to message {:filename filename :result :ok})
      (catch #?(:bb clojure.lang.ExceptionInfo :clj clojure.lang.Compiler$CompilerException) ex
        (respond-to message {:filename filename :result :fail :reason :compiler-ex :ex (Throwable->str ex)})))
    (catch FileNotFoundException ex
      (respond-to message {:filename filename :result :fail :reason :not-found :ex (Throwable->str ex)}))))
