(ns tutkain.base64
  (:import
   (clojure.lang LineNumberingPushbackReader)
   (java.io ByteArrayInputStream InputStreamReader FileNotFoundException)
   (java.util Base64 Base64$Decoder)))

(def ^Base64$Decoder base64-decoder
  (Base64/getDecoder))

(defn base64-reader
  ^LineNumberingPushbackReader [blob]
  (->
    base64-decoder
    (.decode ^String blob)
    (ByteArrayInputStream.)
    (InputStreamReader.)
    (LineNumberingPushbackReader.)))

(defn load-base64
  ([blob] (load-base64 blob "NO_SOURCE_FILE" "NO_SOURCE_PATH"))
  ([blob path filename]
   #?(:bb (binding [*file* path]
            (load-string (String. (.decode base64-decoder blob) "UTF-8")))
      :clj (with-open [reader (base64-reader ^bytes blob)]
             (clojure.lang.Compiler/load reader path filename)))))
