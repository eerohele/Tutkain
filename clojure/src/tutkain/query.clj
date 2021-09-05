(ns tutkain.query
  (:require
   [tutkain.backchannel :refer [handle respond-to]]
   [tutkain.lookup :as lookup]))

(defn ^:private add-type
  [{:keys [macro arglists] :as meta}]
  (assoc meta :type (cond macro :macro arglists :function :else :var)))

(defmethod handle :apropos
  [{:keys [pattern] :as message}]
  (when-some [re (some-> pattern not-empty re-pattern)]
    (let [metas (sort-by :name
                  (sequence
                    (comp
                      (map ns-interns)
                      (mapcat vals)
                      (map meta)
                      (filter :doc)
                      (filter (fn [{:keys [doc name]}]
                                (or
                                  (re-find (re-matcher re doc))
                                  (re-find (re-matcher re (str name))))))
                      (map lookup/prep-meta)
                      (map add-type))
                    (all-ns)))]
      (respond-to message {:vars metas}))))

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
      (when-some [vars (sort-by :name
                         (eduction
                           (map val)
                           (map meta)
                           (map lookup/prep-meta)
                           (map add-type)
                           (ns-publics sym-ns)))]
        (respond-to message {:symbol (name sym)
                             :vars vars})))))
