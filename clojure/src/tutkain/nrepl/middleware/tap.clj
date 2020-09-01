(ns tutkain.nrepl.middleware.tap
  (:require
   [tutkain.fipp.v0v6v23.fipp.edn :as pprint]
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
          (let [tap (with-out-str (pprint/pprint value))
                response (response-for message {:tap tap})]
            (transport/send transport (dissoc response :id)))))
      (handler message))))


(middleware/set-descriptor! #'wrap-tap
  {:requires #{"clone"}
   :expects #{}
   :handles {"tutkain/add-tap" {:doc ""
                                :requires {}
                                :optional {}
                                :returns {"tap" ""}}}})
