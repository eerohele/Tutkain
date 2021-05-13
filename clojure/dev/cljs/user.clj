(ns user
  (:require
   [cljs.build.api :as build]
   [cljs.repl :as repl]
   [cljs.repl.browser :as browser]))

(comment
  (require
    '[tutkain.cljs :refer [*compiler-env*]]
    '[tutkain.repl :refer [*out-fn*]])

  (build/build "dev/src"
    {:main 'my.app
     :output-to "out/main.js"
     :target :browser
     :verbose false}
    *compiler-env*)

  (repl/repl (browser/repl-env :launch-browser false)
    :watch "dev/src"
    :output-dir "out"
    :need-prompt (constantly false)
    :prompt (constantly "")
    :print #(*out-fn* :ret %)
    :caught (fn [ex & _]
              (*out-fn* :err (-> ex Throwable->map repl/ex-triage repl/ex-str)))
    :compiler-env *compiler-env*)
  )
