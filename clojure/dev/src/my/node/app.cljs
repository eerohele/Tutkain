(ns my.node.app
  (:require
   [cljs.nodejs :as node]
   [clojure.string :as string]))

(def fs (node/require "fs"))

(defn -main
  [& _]
  (println "Hello, world!"))

(defn read-file
  [^js path]
  (.readFileSync fs path #js {:encoding "utf-8"}))

(comment
  (let [lines (string/split (read-file "/etc/hosts") #"\n")]
    (remove #(string/starts-with? % "#") lines))
  ,)
