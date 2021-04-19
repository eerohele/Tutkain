(ns my.app
  (:require
   [cljs.pprint :as pprint]
   [cljs.spec.alpha :as spec]
   [my.other :as other]))

(defn ^:dev/after-load ^:after-load start
  []
  (->
    js/document
    (.getElementById "app")
    (.-innerHTML)
    (set! ::running)))

(defn stop
  []
  (->
    js/document
    (.getElementById "app")
    (.-innerHTML)
    (set! ::stopped)))

(defonce go (do (start) true))

(comment
  ::other/keyword

  (start)
  (stop)
  (pprint/pprint {:a 1})
  )
