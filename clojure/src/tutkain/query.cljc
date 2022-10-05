(ns tutkain.query
  (:refer-clojure :exclude [loaded-libs])
  (:require
   [clojure.core :as core]
   [tutkain.backchannel :refer [handle respond-to]]
   [tutkain.lookup :as lookup]))

(defn ^:private meta-with-type
  [var]
  (when (var? var)
    (let [{:keys [macro arglists] :as m} (meta var)
          v (var-get var)]
      (assoc m :type (cond
                       (= clojure.lang.MultiFn (class v)) :multimethod
                       (and (map? v) (contains? v :impls)) :protocol
                       macro :macro
                       arglists :function
                       :else :var)))))

(defmethod handle :apropos
  [{:keys [pattern] :as message}]
  (when-some [re (some-> pattern not-empty re-pattern)]
    (let [vars (eduction
                 (map ns-publics)
                 (mapcat vals)
                 (map meta-with-type)
                 (filter (fn [{:keys [doc name]}]
                           (or
                             (and doc (re-find (re-matcher re doc)))
                             (re-find (re-matcher re (str name))))))
                 (map lookup/prep-meta)
                 (all-ns))]
      (respond-to message {:results (sort-by (juxt :ns :name) vars)}))))

(defmethod handle :dir
  [{:keys [ns sym] :as message}]
  (let [sym (symbol sym)
        ns (or (some-> ns symbol find-ns) (the-ns 'user))]
    (when-some [sym-ns (or
                         ;; symbol naming ns
                         (some-> sym symbol find-ns)
                         ;; ns alias symbol
                         (get (ns-aliases ns) sym)
                         ;; non-ns symbol
                         (symbol (namespace (symbol (ns-resolve ns sym)))))]
      (let [vars (eduction
                   (map val)
                   (map meta-with-type)
                   (map lookup/prep-meta)
                   (ns-publics sym-ns))]
        (respond-to message {:symbol sym
                             :results (sort-by :name vars)})))))

(defmulti loaded-libs :dialect)

(defmethod loaded-libs :clj
  [message]
  (let [libs (eduction
               (map lookup/ns-meta)
               (map lookup/prep-meta)
               (filter :file)
               (remove (comp #{"NO_SOURCE_PATH"} :file))
               #?(:bb [] :clj (core/loaded-libs)))]
    (respond-to message {:results libs})))

(defmethod loaded-libs :bb [_])

(defmethod handle :loaded-libs
  [message]
  (loaded-libs message))

(defmulti intern-mappings :dialect)

(defmethod intern-mappings :clj
  [{:keys [ns] :as message}]
  (when-some [ns (some-> ns find-ns)]
    (let [interns (eduction
                    (map val)
                    (map meta-with-type)
                    (map lookup/prep-meta)
                    (ns-interns ns))]
      (respond-to message {:results interns}))))

(defmethod handle :intern-mappings
  [message]
  (intern-mappings message))

(defmulti remove-namespace-mapping :dialect)

(defmethod remove-namespace-mapping :clj
  [{:keys [ns sym] :as message}]
  (try
    (ns-unmap (some-> ns find-ns) sym)
    (respond-to message {:result :ok :ns ns :sym sym})
    (catch Exception _
      (respond-to message {:result :nok}))))

(defmethod handle :remove-namespace-mapping
  [message]
  (remove-namespace-mapping message))

(defmulti alias-mappings :dialect)

(defmethod alias-mappings :clj
  [{:keys [ns] :as message}]
  (when-some [ns (some-> ns find-ns)]
    (let [aliases (map (fn [[alias ns]] {:type :namespace
                                         :doc (-> ns ns-name str)
                                         :name alias})
                    (ns-aliases ns))]
      (respond-to message {:results aliases}))))

(defmethod handle :alias-mappings
  [message]
  (alias-mappings message))

(defmulti remove-namespace-alias :dialect)

(defmethod remove-namespace-alias :clj
  [{:keys [ns sym] :as message}]
  (try
    (ns-unalias (some-> ns find-ns) sym)
    (respond-to message {:result :ok :ns ns :sym sym})
    (catch Exception _
      (respond-to message {:result :nok}))))

(defmethod handle :remove-namespace-alias
  [message]
  (remove-namespace-alias message))
