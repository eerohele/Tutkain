(ns user
  (:require
   [shadow.cljs.devtools.server :as server]
   [shadow.cljs.devtools.api :as shadow]))

(comment
  (server/start!)
  (shadow/watch :browser)

  (do
    (server/start!)
    (shadow/watch :node-script)

    (->
      (ProcessBuilder. (into-array String ["node" "out/script.js"]))
      (.inheritIO)
      (.start)))

  (server/stop!)
  :cljs/quit
  )
