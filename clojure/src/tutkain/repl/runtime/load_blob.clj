(ns tutkain.repl.runtime.load-blob
  (:require
   [tutkain.repl.runtime.repl :refer [handle pp-str response-for]])
  (:import
   (clojure.lang Compiler LineNumberingPushbackReader)
   (java.io File StringReader)))

(defmulti load-blob :dialect)

(defmethod load-blob :default
  [{:keys [code file out-fn] :as message}]
  (try
    (let [file-name (some-> file File. .getName)
          val (Compiler/load (LineNumberingPushbackReader. (StringReader. code)) file file-name)]
      (out-fn (response-for message {:tag :ret :val (pr-str val)})))
    (catch Throwable ex
      (out-fn (response-for message {:tag :ret
                                     :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                                     :exception true})))))

(defmethod handle :load
  [message]
  (load-blob message))
