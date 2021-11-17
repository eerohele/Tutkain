(ns tutkain.analyzer
  (:require
   [clojure.tools.analyzer.jvm :as analyzer.jvm]
   [clojure.tools.analyzer.ast :as analyzer.ast]
   [clojure.tools.analyzer.passes :as passes]
   [clojure.tools.analyzer.passes.source-info :as source-info]
   [clojure.tools.analyzer.passes.uniquify :as uniquify]
   [clojure.tools.reader :as reader]
   [tutkain.base64 :refer [base64-reader]]
   [tutkain.backchannel :as bc :refer [handle respond-to]])
  (:import
   (clojure.lang LineNumberingPushbackReader)))

#_(set! *warn-on-reflection* true)

(def ^:private analyzer-passes
  (passes/schedule #{#'source-info/source-info #'uniquify/uniquify-locals}))

(def ^:private reader-opts
  {:eof ::EOF :features #{:clj :t.a.jvm} :read-cond :allow})

(defn reader->nodes
  "Given a file path, namespace, line, column, and a
  LineNumberingPushbackReader, read code from the reader in the context of the
  file and the namespace, and return a lazy sequence of ASTs nodes for the
  code."
  [path ns line column ^LineNumberingPushbackReader reader]
  (binding [analyzer.jvm/run-passes analyzer-passes
            *ns* ns
            *file* path]
    (let [reader (doto reader
                   (.setLineNumber (int line))
                   (bc/set-column! (int column)))]
      (sequence
        (comp
          (take-while #(not (identical? ::EOF %)))
          (map analyzer.jvm/analyze)
          (mapcat analyzer.ast/nodes))
        (repeatedly #(reader/read reader-opts reader))))))

(defn node->position
  "Given an tools.analyzer node, return the position information for that
  node."
  [{form :form {:keys [line column end-column]} :env}]
  {:line line
   :column column
   :form form
   :end-column (if (and end-column (zero? end-column))
                 (-> form str count (+ column))
                 end-column)})

(defn index-by-position
  "Given a sequence of tools.analyzer AST nodes, filter nodes that represent a
  local or a binding symbol, and return a map where the key is the position of
  the node and the val is the unique name of the node."
  [nodes]
  (into {}
    (comp
      (filter (comp #{:binding :local} :op))
      (map (juxt node->position :name)))
    nodes))

(defn local-positions
  "Given a map of data about a local, find all positions in :context where the
  local is used. Keys:

  :context -- The Base64-encoded code string where the local is used.
  :form -- The form (symbol) whose positions to search.
  :file (Optional) -- The path to the file that contains :context.
  :ns (Optional) -- The namespace that contains :context.
  :start-line -- The line number where :context begins.
  :start-column -- The column number where :context begins.
  :line -- The line number of :form.
  :column -- The column number where :form begins.
  :end-column -- The column number where :form ends.

  See analyzer.repl for examples."
  [{:keys [context form file ns start-line start-column line column end-column]}]
  (with-open [reader (base64-reader context)]
    (let [nodes (reader->nodes file ns start-line start-column reader)
          position->unique-name (index-by-position nodes)
          position {:form (-> form name symbol)
                    :line line
                    :column column
                    :end-column end-column}
          unique-name->node (group-by :name nodes)
          unique-name (position->unique-name position)]
      (map node->position (unique-name->node unique-name)))))

(defn ^:private parse-namespace
  [ns]
  (or (some-> ns symbol find-ns) (the-ns 'user)))

(defmethod handle :locals
  [message]
  (try
    (let [positions (->
                      message
                      (update :form symbol)
                      (update :ns parse-namespace)
                      local-positions)]
      (respond-to message {:positions positions}))
    (catch Throwable ex
      (respond-to message {:tag :ret :debug true :val (pr-str (Throwable->map ex))}))))
