(ns user
  (:require
   [cljs.repl :as repl]
   [figwheel.main.api :as figwheel]))

(comment
  (figwheel/start
    {:id "dev"

     :options
     {:main 'my.app
      :output-dir "resources/public"
      :asset-path ""}

     :config
     {:mode :serve
      :asset-path ""
      :open-url false}})

  (figwheel/stop-all)

  (repl/repl (figwheel/repl-env "dev")
    :need-prompt (constantly false)
    :prompt (constantly ""))

  :cljs/quit)
