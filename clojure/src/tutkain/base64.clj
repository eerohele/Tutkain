(ns tutkain.base64
  (:require
   [tutkain.backchannel :refer [handle respond-to]])
  (:import
   (clojure.lang Compiler Compiler$CompilerException LineNumberingPushbackReader)
   (java.io ByteArrayInputStream InputStreamReader FileNotFoundException)
   (java.util Base64)))

(def ^:private base64-decoder
  (Base64/getDecoder))

(defn ^LineNumberingPushbackReader base64-reader
  [blob]
  (->
    base64-decoder
    (.decode blob)
    (ByteArrayInputStream.)
    (InputStreamReader.)
    (LineNumberingPushbackReader.)))

(defmethod handle :load-base64
  [{:keys [blob path filename requires] :as message}]
  (try
    (some->> requires (run! require))
    (with-open [reader (base64-reader blob)]
      (try
        (Compiler/load reader path filename)
        (respond-to message {:filename filename :result :ok})
        (catch Compiler$CompilerException ex
          (respond-to message {:filename filename :result :fail :reason :compiler-ex :ex (Throwable->map ex)}))))
    (catch FileNotFoundException ex
      (respond-to message {:filename filename :result :fail :reason :not-found :ex (Throwable->map ex)}))))
