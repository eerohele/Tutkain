(ns tutkain.query
  (:require
   [tutkain.backchannel :refer [handle respond-to]]
   [tutkain.lookup :as lookup]))

(defn ^:private meta-with-type
  [var]
  (let [{:keys [macro arglists] :as m} (meta var)
        v (var-get var)]
    (assoc m :type (cond
                     (= clojure.lang.MultiFn (class v)) :multimethod
                     (and (map? v) (contains? v :impls)) :protocol
                     macro :macro
                     arglists :function
                     :else :var))))

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
                         (some-> (ns-resolve ns sym) .ns))]
      (let [vars (eduction
                   (map val)
                   (map meta-with-type)
                   (map lookup/prep-meta)
                   (ns-publics sym-ns))]
        (respond-to message {:symbol (name sym)
                             :results (sort-by :name vars)})))))
