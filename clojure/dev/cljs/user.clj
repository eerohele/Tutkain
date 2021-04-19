(ns user
  (:require
   [cljs.build.api :as build]
   [cljs.env :as env]
   [cljs.repl :as repl]
   [cljs.repl.browser :as browser]))

(comment
  (build/build ["dev/src"]
    {:main 'my.app
     :output-to "out/app.js"
     :output-dir "out"
     :target :browser}
    tutkain.repl.runtime.cljs/*compiler-env*)

  (repl/repl (browser/repl-env)
    :need-prompt (constantly false)
    :prompt (constantly ""))

  :cljs/quit
  )
