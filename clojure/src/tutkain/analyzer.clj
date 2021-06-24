(ns tutkain.analyzer
  (:require
   [clojure.tools.analyzer.jvm :as analyzer.jvm]
   [clojure.tools.analyzer.ast :as analyzer.ast]
   [clojure.tools.analyzer.passes :as passes]
   [clojure.tools.analyzer.passes.source-info :as source-info]
   [clojure.tools.analyzer.passes.uniquify :as uniquify]
   [clojure.tools.reader :as reader]
   [tutkain.backchannel :as bc :refer [handle respond-to]])
  (:import
   (clojure.lang LineNumberingPushbackReader)
   (java.io StringReader)))

(def ^:private analyzer-passes
  (passes/schedule #{#'source-info/source-info #'uniquify/uniquify-locals}))

(def ^:private reader-opts
  {:features #{:clj :t.a.jvm} :read-cond :allow})

(defn string->nodes
  "Given a file path, namespace, line, column, and a code string, read the
  string in the context of the file and the namespace, and return a lazy
  sequence of ASTs nodes resulting from analyzing the code."
  [path ns line column string]
  (binding [analyzer.jvm/run-passes analyzer-passes
            *ns* ns
            *file* path]
    (let [eof (Object.)
          reader (doto
                   (LineNumberingPushbackReader. (StringReader. string))
                   (.setLineNumber (int line))
                   (bc/set-column! (int column)))]
      (sequence
        (comp
          (take-while #(not (identical? eof %)))
          (map analyzer.jvm/analyze)
          (mapcat analyzer.ast/nodes))
        (repeatedly #(reader/read (assoc reader-opts :eof eof) reader))))))

(defn node->position
  "Given an tools.analyzer node, return the position information for that
  node."
  [{form :form {:keys [line column]} :env}]
  {:line line
   :column column
   :form form
   :end-column (-> form str count (+ column))})

(defn index-by-position
  "Given a sequence of AST nodes, return a map where the key is the position
  of the node and the val is the unique name of the node."
  [nodes]
  (into {}
    (comp
      (map (juxt node->position :name))
      (filter second))
    nodes))

(defn local-positions
  "Given a map of data about a local, find all positions in :context where the
  local is used. Keys:

  :context -- The code string where the local symbol is used.
  :form -- The form whose positions to search.
  :file (Optional) -- The path to the file that contains :context.
  :ns (Optional) -- The namespace that contains :context.
  :start-line -- The line number where :context begins.
  :start-column -- The column number where :context begins.
  :line -- The line number of :form.
  :column -- The column number where :form begins.
  :end-column -- The column number where :form ends."
  [{:keys [context form file ns start-line start-column line column end-column]}]
  (let [nodes (string->nodes file ns start-line start-column context)
        position->unique-name (index-by-position nodes)
        position {:form form :line line :column column :end-column end-column}]
    (when-some [unique-name (get position->unique-name position)]
      (eduction
        (filter #(= unique-name (:name %)))
        (map node->position)
        nodes))))

(defn ^:private parse-namespace
  [ns]
  (or (some-> ns symbol find-ns) (the-ns 'user)))

(defmethod handle :locals
  [message]
  (try
    (respond-to message {:positions (local-positions (update message :ns parse-namespace))})
    (catch Throwable ex
      (respond-to message {:tag :ret :debug true :val (pr-str (Throwable->map ex))}))))
