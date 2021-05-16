(ns tutkain.load-blob
  (:require
   [tutkain.repl :refer [handle pp-str respond-to]])
  (:import
   (clojure.lang Compiler LineNumberingPushbackReader)
   (java.io File StringReader)))

(defmulti load-blob :dialect)

(defmethod load-blob :default
  [{:keys [code file] :as message}]
  (try
    (with-open [reader (LineNumberingPushbackReader. (StringReader. code))]
      (locking eval-lock
        (let [file-name (some-> file File. .getName)
              val (Compiler/load reader file file-name)]
          (respond-to message {:tag :ret :val (pr-str val)}))))
    (catch Throwable ex
      (respond-to message {:tag :ret
                           :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                           :exception true}))))

(defmethod handle :load
  [message]
  (load-blob message))
