(ns my.app
  (:require
   [clojure.browser.repl :as repl]
   [cljs.pprint :as pprint]
   [cljs.spec.alpha :as spec]
   [my.other :as other]))

(defonce conn
  (repl/connect "http://localhost:9000/repl"))

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
  )
