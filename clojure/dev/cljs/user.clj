(ns user
  (:require
   [cljs.analyzer.api :as analyzer.api]
   [cljs.build.api :as build]
   [cljs.env :as env]
   [cljs.repl :as repl]
   [cljs.repl.browser :as browser]))

(comment
  (build/build "dev/src"
    {:main 'my.app
     :output-to "out/main.js"
     :target :browser
     :verbose false})

  (repl/repl (browser/repl-env)
    :init #(println :done)
    :watch "dev/src"
    :output-dir "out"
    :need-prompt (constantly false)
    :prompt (constantly "")
    :print tutkain.repl/*print*
    :caught tutkain.repl/*caught*)

  :cljs/quit
  )
