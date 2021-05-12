(ns user
  (:require
   [cljs.build.api :as build]
   [cljs.repl :as repl]
   [cljs.repl.browser :as browser]))

(comment
  (require
    '[tutkain.cljs :refer [*compiler-env*]]
    '[tutkain.repl :refer [*print* *caught*]])

  (build/build "dev/src"
    {:main 'my.app
     :output-to "out/main.js"
     :target :browser
     :verbose false}
    *compiler-env*)

  (repl/repl (browser/repl-env)
    :init #(println :done)
    :watch "dev/src"
    :output-dir "out"
    :need-prompt (constantly false)
    :prompt (constantly "")
    :print *print*
    :caught *caught*
    :compiler-env *compiler-env*)
  )
