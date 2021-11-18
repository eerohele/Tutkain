(ns tutkain.analyzer
  (:require
   [clojure.tools.analyzer.ast :as analyzer.ast]
   [clojure.tools.reader :as reader]
   [tutkain.backchannel :as bc :refer [handle]])
  (:import
   (clojure.lang LineNumberingPushbackReader)))

#_(set! *warn-on-reflection* true)

(defn analyze
  "Read code from a reader and return a seq of ASTs nodes for the code.

  Keyword arguments:
    :analyzer -- A fn that takes a form and returns an AST
    :reader -- A LineNumberingPushbackReader to read from
    :start-column -- The column number to set the reader to
    :start-line -- The line number to set the reader to
    :reader-opts -- A map of options to pass to clojure.tools.reader/read
    :xform -- A transducer to transform resulting sequence of AST nodes (optional)"
  [& {:keys [^LineNumberingPushbackReader reader analyzer reader-opts start-column start-line xform]
      :or {xform (map identity)}}]
  (let [reader (doto reader
                 (.setLineNumber (int start-line))
                 (bc/set-column! (int start-column)))]
    (eduction
      (take-while #(not (identical? ::EOF %)))
      (map analyzer)
      (mapcat analyzer.ast/nodes)
      xform
      (repeatedly #(reader/read (assoc reader-opts :eof ::EOF) reader)))))

(defn node->position
  "Given an tools.analyzer node, return the position information for that
  node."
  [{form :form {:keys [line column end-column]} :env}]
  {:line line
   :column column
   :form form
   :end-column (if (or
                     (and column (nil? end-column))
                     (and end-column (zero? end-column)))
                 (-> form str count (+ column))
                 end-column)})

(defn index-by-position
  "Given a sequence of tools.analyzer AST nodes, filter nodes that represent a
  local or a binding symbol, and return a map where the key is the position of
  the node and the val is the unique name of the node."
  [nodes]
  (into {}
    (comp
      (filter (every-pred :form (comp #{:binding :local} :op)))
      (map (juxt node->position :name)))
    nodes))

(defn local-positions
  "Given a seq of tools.analyzer AST nodes and map indicating the position of a
  local, return all positions where that local is used."
  [nodes position]
  (let [position->unique-name (index-by-position nodes)]
    (when-some [unique-name (get position->unique-name position)]
      (eduction
        (filter #(= unique-name (:name %)))
        (map node->position)
        nodes))))

(defn position
  "Given a :locals message, return the position of the local in the message."
  [{:keys [form line column end-column]}]
  {:form (-> form symbol name symbol)
   :line line
   :column column
   :end-column end-column})

(defmulti locals :dialect)

(defmethod handle :locals
  [message]
  (locals message))
