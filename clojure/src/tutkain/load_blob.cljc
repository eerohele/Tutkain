(ns tutkain.load-blob
  (:require
   [clojure.java.io :as io]
   [tutkain.format :refer [pp-str]]
   [tutkain.base64 :refer [read-base64]]
   [tutkain.backchannel :refer [handle relative-to-classpath-root respond-to]])
  (:import
   (java.io Writer)))

(defmethod handle :load
  [{:keys [eval-lock eval-context code file] :as message}]
  (try
    (let [file-name (some-> file io/file .getName)
          val (locking eval-lock (with-bindings (:thread-bindings @eval-context {})
                                   (read-base64 code (relative-to-classpath-root file) file-name)
                                   (.flush ^Writer *err*)))]
      (respond-to message {:tag :ret
                           :val (pp-str val)}))
    (catch Throwable ex
      (swap! eval-context assoc-in [:thread-bindings #'*e] ex)
      (respond-to message {:tag :ret
                           :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                           :exception true}))))

