(ns tutkain.analyzer.jvm
  (:require
   [clojure.tools.analyzer.jvm :as analyzer.jvm]
   [clojure.tools.analyzer.passes :as passes]
   [clojure.tools.analyzer.passes.source-info :as source-info]
   [clojure.tools.analyzer.passes.uniquify :as uniquify]
   [tutkain.analyzer :as analyzer]
   [tutkain.base64 :refer [base64-reader]]
   [tutkain.rpc :refer [respond-to]]))

(def analyzer-passes
  {:local-instances (passes/schedule #{#'source-info/source-info #'uniquify/uniquify-locals})
   :local-symbols (passes/schedule #{#'source-info/source-info})})

(defn ^:private parse-namespace
  [ns]
  (or (some-> ns symbol find-ns) (the-ns 'user)))

(def reader-opts
  {:features #{:clj :t.a.jvm} :read-cond :allow})

(defn analyze
  [passes forms]
  (analyzer/analyze
    :forms forms
    :analyzer (fn [form]
                (binding [analyzer.jvm/run-passes (analyzer-passes passes)]
                  (analyzer.jvm/analyze form)))))

(defmethod analyzer/local-instances :default
  [{:keys [enclosing-sexp file ns start-column start-line] :as message}]
  (try
    (binding [*file* file
              *ns* (parse-namespace ns)]
      (let [forms (with-open [reader (base64-reader enclosing-sexp)]
                    (analyzer/read-forms reader reader-opts start-line start-column))
            nodes (analyze :local-instances forms)
            positions (analyzer/local-positions nodes (analyzer/position message))]
        (respond-to message {:positions positions})))
    (catch Throwable ex
      (respond-to message {:tag :ret :debug true :val (pr-str (Throwable->map ex))}))))

(defn local-symbols
  [{:keys [forms file ns line column]}]
  (when (and (seq forms) (nat-int? line) (nat-int? column))
    (let [nodes (binding [*file* file
                          *ns* ns]
                  (analyze :local-symbols forms))]
      (analyzer/local-symbols line column nodes))))
