(ns tutkain.repl.runtime.lookup
  (:require
   [clojure.java.io :as io]
   [tutkain.repl.runtime.repl :refer [handle pp-str response-for]]))

(set! *warn-on-reflection* true)

;; Adapted from nrepl.util.lookup

(defn special-sym-meta
  [sym]
  (let [f (requiring-resolve 'clojure.repl/special-doc)]
    (assoc (f sym)
      :ns "clojure.core"
      :file "clojure/core.clj"
      :special-form "true")))

(defn normal-sym-meta
  [ns sym]
  (some-> (ns-resolve ns sym) meta))

(defn sym-meta
  [ns sym]
  (if (special-symbol? sym)
    (special-sym-meta sym)
    (normal-sym-meta ns sym)))

(defn ^:private remove-empty
  [m]
  (reduce-kv #(if (and (seqable? %3) (empty? %3))
                %1
                (assoc %1 %2 %3))
    {}
    m))

(defn lookup
  [ns sym]
  (some->
    (sym-meta ns sym)
    (select-keys [:ns :name :file :column :line :arglists :doc])
    (update :ns str)
    (update :file #(let [s (str %)]
                     (or (some-> s io/resource str) s)))
    (update :arglists str)
    (remove-empty)))

(defmethod handle :lookup
  [{:keys [sym ns out-fn] :as message}]
  (try
    (when-some [result (lookup (or (some-> ns symbol) (the-ns 'user)) (symbol sym))]
      (out-fn (response-for message {:info result})))
    (catch Throwable ex
      (out-fn (response-for message {:ex (pp-str (Throwable->map ex))})))))
