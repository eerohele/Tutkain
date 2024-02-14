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
  {:local-instances (passes/schedule #{#'source-info/source-info #'uniquify/uniquify-locals})
   :local-symbols (passes/schedule #{#'source-info/source-info})})

(defn ^:private parse-namespace
  [ns]
  (or (some-> ns symbol find-ns) (the-ns 'user)))

(defmethod analyzer/local-instances :default
  [{:keys [enclosing-sexp file ns start-column start-line] :as message}]
  (try
    (binding [*file* file
              *ns* (parse-namespace ns)]
      (let [forms (with-open [reader (base64-reader enclosing-sexp)]
                    (analyzer/read-forms reader {:features #{:clj :t.a.jvm} :read-cond :allow} start-line start-column))
            nodes (binding [analyzer.jvm/run-passes (analyzer-passes :local-instances)]
                    (analyzer/analyze
                      :forms forms
                      :analyzer analyzer.jvm/analyze))
            positions (analyzer/local-positions nodes (analyzer/position message))]
        (respond-to message {:positions positions})))
    (catch Throwable ex
      (respond-to message {:tag :ret :debug true :val (pr-str (Throwable->map ex))}))))

(defn local-symbols
  [{:keys [forms file ns line column]}]
  (when (seq forms)
    (let [nodes (binding [*file* file
                          *ns* ns]
                  (analyzer/analyze
                    :forms forms
                    :analyzer (fn [form]
                                (binding [analyzer.jvm/run-passes (analyzer-passes :local-symbols)]
                                  (analyzer.jvm/analyze form)))))]
      (analyzer/local-symbols line column nodes))))

(comment
  (tutkain.analyzer.jvm/local-symbols {:forms forms :file file :ns (find-ns 'tutkain.analyzer.jvm) :line 1 :column 1})
  ,,,)
