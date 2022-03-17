(ns tutkain.load-blob
  (:require
   [tutkain.format :refer [pp-str]]
   [tutkain.base64 :refer [base64-reader]]
   [tutkain.backchannel :refer [handle respond-to]])
  (:import
   (clojure.lang Compiler)
   (java.io File)))

(defmethod handle :load
  [{:keys [eval-context code file] :as message}]
  (try
    (with-open [reader (base64-reader code)]
      (let [file-name (some-> file File. .getName)
            val (Compiler/load reader (or file "NO_SOURCE_FILE") file-name)]
        (respond-to message {:tag :ret
                             :val (pp-str val)})))
    (catch Throwable ex
      (swap! eval-context assoc-in [:thread-bindings #'*e] ex)
      (respond-to message {:tag :ret
                           :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                           :exception true}))))

