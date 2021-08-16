(ns tutkain.load-blob
  (:require
   [tutkain.format :refer [pp-str]]
   [tutkain.backchannel :refer [base64-reader handle respond-to]])
  (:import
   (java.io File)))

(defmethod handle :load
  [{:keys [code file] :as message}]
  (try
    (with-open [reader (base64-reader code)]
      (let [file-name (some-> file File. .getName)
            val (Compiler/load reader (or file "NO_SOURCE_FILE") file-name)]
        (respond-to message {:tag :ret
                             :val (pp-str val)})))
    (catch Throwable ex
      (respond-to message {:tag :ret
                           :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                           :exception true}))))

