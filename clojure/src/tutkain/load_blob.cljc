(ns tutkain.load-blob
  (:require
   [tutkain.format :refer [pp-str]]
   [tutkain.base64 :refer [read-base64]]
   [tutkain.backchannel :refer [handle respond-to]])
  (:import
   (java.io File)))

(defmethod handle :load
  [{:keys [eval-lock eval-context code file] :as message}]
  (try
    (let [file-name (some-> file File. .getName)
          val (locking eval-lock (read-base64 code (or file "NO_SOURCE_FILE") file-name))]
      (respond-to message {:tag :ret
                           :val (pp-str val)}))
    (catch Throwable ex
      (swap! eval-context assoc-in [:thread-bindings #'*e] ex)
      (respond-to message {:tag :ret
                           :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                           :exception true}))))

