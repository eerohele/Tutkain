(ns tutkain.lookup
  (:require
   [clojure.java.io :as io]
   #?@(:bb [] :clj [[clojure.spec.alpha :as spec]])
   [tutkain.format :refer [pp-str]]
   [tutkain.backchannel :refer [handle respond-to]]))

#_(set! *warn-on-reflection* true)

;; Adapted from nrepl.util.lookup

(defn special-sym-meta
  "Given a Clojure special form, return metadata for that special form."
  [sym]
  (let [f (requiring-resolve 'clojure.repl/special-doc)]
    (assoc (f sym)
      :ns (the-ns 'clojure.core)
      :file "clojure/core.clj"
      :special-form "true")))

(defn fnspec
  "Given a var, return a description of the fnspec of that var, if any."
  [v]
  #?(:bb {}
     :clj (into {}
            (keep #(some->> (get (spec/get-spec v) %) spec/describe pr-str (vector %)))
            [:args :ret :fn])))

(defn ns-meta
  [sym]
  (when-some [ns (find-ns sym)]
    (merge (meta ns)
      {:name (ns-name ns)
       :file (->> ns ns-interns vals first meta :file)
       :line 0
       :column 0
       :type :namespace})))

(defn sym-meta
  "Given an ns symbol and a symbol, return the metadata for the var that symbol
  names.

  If the symbol names a namespace, use the path of the first intern mapping in
  that namespace as the :file value.

  If the symbol names a function that has an fnspec, describe the fnspec under
  the :fnspec key."
  [ns sym]
  (or
    (ns-meta sym)
    (let [var (ns-resolve ns sym)
          fnspec* (fnspec var)]
      (cond-> (if (special-symbol? sym)
                (special-sym-meta sym)
                (some-> var meta))
        (seq fnspec*) (assoc :fnspec fnspec*)))))

(defn ^:private remove-empty
  [m]
  (reduce-kv #(if (and (seqable? %3) (empty? %3))
                %1
                (assoc %1 %2 %3))
    {}
    m))

(defn resolve-file
  "Given the value of the :file key of a var metadata map, resolve the file
  path against the current classpath."
  [file]
  (when file
    (let [s (str file)]
      (or (some-> s io/resource str) s))))

(defn prep-meta
  [{sym-name :name sym-ns :ns protocol :protocol :as m}]
  (if protocol
    (recur (assoc (meta protocol) :name sym-name :arglists (:arglists m) :doc (:doc m)))
    (some->
      m
      (select-keys [:name :file :column :line :arglists :doc :fnspec :type])
      (assoc :ns (some-> sym-ns ns-name name))
      (assoc :name (cond
                     (qualified-symbol? sym-name)
                     sym-name
                     (and (some? sym-ns) (nil? sym-name))
                     (symbol (-> sym-ns ns-name str) (name sym-name))
                     :else sym-name))
      (update :file resolve-file)
      (update :arglists #(map pr-str %))
      (remove-empty))))

(defn lookup
  "Given an ns symbol and a string representation of an ident, return selected
  metadata of the var it names.

  If the ident is a keyword that names a spec, describe the spec.

  Otherwise, if it's a symbol, describe the var that symbol names."
  [ns ident]
  (let [ns (or (some-> ns symbol find-ns) (the-ns 'user))
        ident (binding [*ns* ns] (read-string ident))]
    (if (keyword? ident)
      #?(:bb {}
         :clj (when-some [spec (some-> ident spec/get-spec spec/describe pr-str)]
                {:name ident
                 :spec spec}))
      (prep-meta (sym-meta ns ident)))))

(defmulti info :dialect)

(defmethod info :default
  [{:keys [ident ns] :as message}]
  (try
    (when-some [result (lookup ns ident)]
      (respond-to message {:info result}))
    (catch Throwable ex
      (respond-to message {:ex (pp-str (Throwable->map ex))}))))

(defmethod handle :lookup
  [message]
  (info message))
