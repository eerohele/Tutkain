(ns tutkain.analyzer.js
  (:require
   [cljs.analyzer]
   [cljs.analyzer.api :as analyzer.api]
   [cljs.env :as env]
   [clojure.tools.reader :as reader]
   [tutkain.analyzer :as analyzer]
   [tutkain.base64 :refer [base64-reader]]
   [tutkain.rpc :refer [respond-to]]
   [tutkain.cljs :refer [compiler-env]]))

(defn ^:private parse-namespace
  [ns]
  (or (some->> ns symbol) 'cljs.user))

(defn ^:private unique-name
  [node]
  (let [name (-> node :info :name)
        shadow-hash (-> node :info :shadow hash)]
    (symbol (str name "__" shadow-hash))))

(def ^:private uniquify
  "A transducer that assigns unique (within a local context) names to AST
  nodes."
  (map
    (fn [node]
      (assoc node :unique-name (unique-name node)))))

(defn analyze
  [start-line start-column reader]
  (let [env (analyzer.api/empty-env)]
    (analyzer/analyze
      :start-line start-line
      :start-column start-column
      :reader reader
      :reader-opts {:read-cond :allow :features #{:cljs}}
      :analyzer #(cljs.analyzer/analyze env %)
      :xform uniquify)))

(defmethod analyzer/locals :cljs
  [{:keys [build-id context start-column start-line file ns] :as message}]
  (try
    (env/with-compiler-env (compiler-env build-id)
      (analyzer.api/no-warn
        (let [ns (parse-namespace ns)]
          (binding [cljs.analyzer/*passes* []
                    *file* file
                    *ns* (create-ns ns)
                    reader/*alias-map* (apply merge
                                         ((juxt :requires :require-macros)
                                          (cljs.analyzer/get-namespace ns)))
                    reader/*data-readers* {}
                    reader/*default-data-reader-fn* (fn [_ val] val)
                    reader/resolve-symbol identity]
            (with-open [reader (base64-reader context)]
              (let [nodes (analyze start-line start-column reader)
                    positions (analyzer/local-positions nodes (analyzer/position message))]
                (respond-to message {:positions positions})))))))
    (catch Throwable ex
      (respond-to message {:tag :ret :debug true :val (pr-str (Throwable->map ex))}))))

