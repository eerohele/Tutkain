(ns tutkain.load-blob
  (:require
   [clojure.java.io :as io]
   [tutkain.format :as format :refer [pp-str]]
   [tutkain.base64 :refer [load-base64]]
   [tutkain.rpc :refer [handle relative-to-classpath-root respond-to]])
  (:import
   (java.io Writer)))

(defmethod handle :load
  [{:keys [eval-lock thread-bindings code file] :as message}]
  (try
    (let [file-name (some-> file io/file .getName)
          val (locking eval-lock
                (with-bindings (merge {#'*ns* (find-ns 'user)} @thread-bindings)
                  (let [ret (load-base64 code (relative-to-classpath-root file) file-name)]
                    (reset! thread-bindings (get-thread-bindings))
                    (.flush ^Writer *err*)
                    ret)))]
      (respond-to message {:tag :ret
                           :val (pp-str val)}))
    (catch Throwable ex
      (swap! thread-bindings assoc #'*e ex)
      (respond-to message {:tag :err
                           :val (format/Throwable->str ex)
                           :exception true}))))

