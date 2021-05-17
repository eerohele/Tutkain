(ns tutkain.lookup
  (:require
   [clojure.java.io :as io]
   [clojure.spec.alpha :as spec]
   [tutkain.repl :refer [handle pp-str respond-to]]))

(set! *warn-on-reflection* true)

;; Adapted from nrepl.util.lookup

(defn special-sym-meta
  [sym]
  (let [f (requiring-resolve 'clojure.repl/special-doc)]
    (assoc (f sym)
      :ns (the-ns 'clojure.core)
      :file "clojure/core.clj"
      :special-form "true")))

(defn fnspec
  [v]
  (into {}
    (keep #(some->> (get (spec/get-spec v) %) spec/describe pr-str (vector %)))
    [:args :ret :fn]))

(defn sym-meta
  [ns sym]
  (if-some [found-ns (find-ns sym)]
    (merge (meta found-ns)
      {:name (ns-name found-ns)
       :file (->> found-ns ns-interns vals first meta :file)
       :line 0
       :column 0})
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
  [file]
  (let [s (str file)]
    (or (some-> s io/resource str) s)))

(defn lookup
  [ns named]
  (let [ns (or (some-> ns symbol find-ns) (the-ns 'user))
        named (binding [*ns* ns] (read-string named))]
    (if (keyword? named)
      (when-some [spec (some-> named spec/get-spec spec/describe pr-str)]
        {:name named
         :spec spec})
      (let [{sym-name :name sym-ns :ns :as m} (sym-meta ns named)]
        (some->
          m
          (select-keys [:name :file :column :line :arglists :doc :fnspec])
          (assoc :ns (some-> sym-ns ns-name name))
          (assoc :name sym-name)
          (update :file resolve-file)
          (update :arglists #(map pr-str %))
          (remove-empty))))))

(defmulti info :dialect)

(defmethod info :default
  [{:keys [named ns] :as message}]
  (try
    (when-some [result (lookup ns named)]
      (respond-to message {:info result}))
    (catch Throwable ex
      (respond-to message {:ex (pp-str (Throwable->map ex))}))))

(defmethod handle :lookup
  [message]
  (info message))
