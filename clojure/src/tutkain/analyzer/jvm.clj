(ns tutkain.analyzer.jvm
  (:require
   [clojure.tools.analyzer.jvm :as analyzer.jvm]
   [clojure.tools.analyzer.passes :as passes]
   [clojure.tools.analyzer.passes.source-info :as source-info]
   [clojure.tools.analyzer.passes.uniquify :as uniquify]
   [tutkain.analyzer :as analyzer]
   [tutkain.base64 :refer [base64-reader]]
   [tutkain.rpc :refer [respond-to]]))

(def ^:private analyzer-passes
  (passes/schedule #{#'source-info/source-info #'uniquify/uniquify-locals}))

(defn ^:private parse-namespace
  [ns]
  (or (some-> ns symbol find-ns) (the-ns 'user)))

(def reader-opts
  {:features #{:clj :t.a.jvm} :read-cond :allow})

(defn analyze
  [start-line start-column reader]
  (analyzer/analyze
    :start-line start-line
    :start-column start-column
    :reader reader
    :reader-opts reader-opts
    :analyzer analyzer.jvm/analyze))

(defmethod analyzer/locals :default
  [{:keys [enclosing-sexp file ns start-column start-line] :as message}]
  (try
    (binding [*file* file
              *ns* (parse-namespace ns)
              analyzer.jvm/run-passes analyzer-passes]
      (with-open [reader (base64-reader enclosing-sexp)]
        (let [nodes (analyze start-line start-column reader)
              positions (analyzer/local-positions nodes (analyzer/position message))]
          (respond-to message {:positions positions}))))
    (catch Throwable ex
      (respond-to message {:tag :ret :debug true :val (pr-str (Throwable->map ex))}))))
