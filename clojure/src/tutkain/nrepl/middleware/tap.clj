(ns tutkain.nrepl.middleware.tap
  (:require
   [clojure.pprint :as pprint]
   [nrepl.middleware :as middleware]
   [nrepl.misc :refer [response-for]]
   [nrepl.transport :as transport]))


(defn wrap-tap
  [handler]
  (fn [{:keys [op transport] :as message}]
    (case op
      "tutkain/add-tap"
      (add-tap
        (fn [value]
          (transport/send transport {:tap (with-out-str (pprint/pprint value))})))
      (handler message))))


(middleware/set-descriptor! #'wrap-tap
  {:requires #{"clone"}
   :expects #{}
   :handles {"tutkain/add-tap" {:doc ""
                                :requires {}
                                :optional {}
                                :returns {"tap" ""}}}})
