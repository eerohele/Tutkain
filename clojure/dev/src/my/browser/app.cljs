(ns my.browser.app
  (:require
   [cljs.pprint :as pprint]
   [cljs.spec.alpha :as spec]
   [my.other :as other])
  (:import
   (goog.date DateTime)))

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

  (pprint/pprint {:a 1})
  (random-uuid)
  (clj->js {:a [1 "b" 'c]})
  (spec/exercise any?)

  (DateTime.)
  ,,,)
