(ns user
  (:require
   [shadow.cljs.devtools.server :as server]
   [shadow.cljs.devtools.api :as shadow]))

(comment
  (server/start!)
  (shadow/watch :browser)
  (shadow/watch :node-script)
  (server/stop!)
  :cljs/quit
  )
