(ns tutkain.repl
  (:require [mranderson.core :as mranderson]))

(def repositories
  {:clojars "https://repo.clojars.org"
   :central "https://repo.maven.apache.org/maven2"})

(def dependencies
  (map #(with-meta % {:inline-dep true}) [['fipp "0.6.23"]]))

(defn munge-dependencies!
  []
  (mranderson/mranderson
    repositories
    dependencies
    {:pname "tutkain"
     :pversion "0.6.0-alpha"
     :pprefix "tutkain"
     :srcdeps "src"}
    {:src-path "src"}))

(comment
  (munge-dependencies!)
  )
