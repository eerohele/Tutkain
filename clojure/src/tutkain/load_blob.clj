(ns tutkain.load-blob
  (:require
   [tutkain.format :refer [pp-str Throwable->str]]
   [tutkain.base64 :refer [base64-reader]]
   [tutkain.backchannel :refer [handle respond-to]])
  (:import
   (clojure.lang Compiler)
   (java.io File)))

(defmethod handle :load
  [{:keys [eval-lock eval-context code file] :as message}]
  (try
    (with-open [reader (base64-reader code)]
      (let [file-name (some-> file File. .getName)
            val (locking eval-lock (Compiler/load reader (or file "NO_SOURCE_FILE") file-name))]
        (respond-to message {:tag :ret
                             :val (pp-str val)})))
    (catch Throwable ex
      (swap! eval-context assoc-in [:thread-bindings #'*e] ex)
      (respond-to message {:tag :ret
                           :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                           :exception true}))))

(defmethod handle :transcribe
  [{:keys [eval-lock eval-context ns code file] :as message}]
  (binding [*ns* (create-ns (or (some-> ns symbol) 'user))
            *file* (or file "NO_SOURCE_PATH")
            *source-path* (or (some-> file File. .getName) "NO_SOURCE_FILE")]
    (with-open [reader (-> code java.io.StringReader. clojure.lang.LineNumberingPushbackReader.)]
      ;; Retain eval lock for the whole transcription process
      (locking eval-lock
        (loop []
          (let [recur? (try
                         (let [[form string] (read+string {:eofthrow false :eof ::eof} reader)]
                           (when-not (identical? ::eof form)
                             (respond-to message {:tag :in :val (str string \newline)})
                             (try
                               (let [ret (eval form)]
                                 (.flush ^java.io.Writer *err*)
                                 (set! *3 *2)
                                 (set! *2 *1)
                                 (set! *1 ret)
                                 (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                                 (respond-to message {:tag :ret :val (pp-str ret)}))
                               true
                               (catch Throwable ex
                                 (set! *e ex)
                                 (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                                 (respond-to message
                                   {:tag :err
                                    :val (Throwable->str ex)
                                    :exception true
                                    :phase :execution})
                                 false))))
                         (catch Throwable ex
                           (set! *e ex)
                           (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                           (respond-to message
                             {:tag :err
                              :val (Throwable->str ex)
                              :phase :read-source
                              :exception true})
                           false))]
            (when recur? (recur))))))))
