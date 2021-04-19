(ns user
  (:require
   [shadow.cljs.devtools.server :as server]
   [shadow.cljs.devtools.api :as shadow]))

(comment
  (server/start!)
  (shadow/watch :app)
  (shadow/repl :app {:prompt false})
  (server/stop!)
  :cljs/quit
  )
