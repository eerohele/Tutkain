(ns tutkain.repl.runtime.load-blob
  (:require
   [clojure.edn :as edn]
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

(defmethod load-blob :cljs
  [{:keys [file out-fn] :as message}]
  ;; FIXME: This doesn't work, because `file` is an absolute path and therefore isn't in
  ;; the classpath.
  (when file
    (let [{:keys [results err]} ((requiring-resolve 'shadow.cljs.devtools.api/cljs-eval)
                                 :app
                                 (format "(cljs.core/load-file \"%s\")" file) {})]
      (when err
        (out-fn (response-for message {:tag :err :val err}))
        (run! #(out-fn (response-for message {:tag :ret :val %})) results)))))

(defmethod handle :load
  [message]
  (load-blob message))
