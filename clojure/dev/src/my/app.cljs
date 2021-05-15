(ns my.app
  (:require
   [cljs.spec.alpha :as spec]
   [my.other :as other]))

(enable-console-print!)

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

  (random-uuid)
  (clj->js {:a [1 "b" 'c]})
  (spec/exercise any?)
  )
