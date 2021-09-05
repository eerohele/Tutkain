(ns tutkain.query
  (:require
   [tutkain.backchannel :refer [handle respond-to]]
   [tutkain.lookup :as lookup]))

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
                      (map (fn [{:keys [macro arglists] :as meta}]
                             (assoc meta :type (cond macro :macro arglists :function :else :var)))))
                    (all-ns)))]
      (respond-to message {:var-metas metas}))))
