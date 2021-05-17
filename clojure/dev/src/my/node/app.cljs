(ns my.node.app
  (:require
   [cljs.nodejs :as node]
   [clojure.string :as string]))

(def fs (node/require "fs"))

(defn -main
  [& _]
  (println "Hello, world!"))

(defn read-file
  [path]
  (.readFileSync fs path #js {:encoding "utf-8"}))

(comment
  (into (sorted-set)
    (comp
      (remove #(string/starts-with? % "#"))
      (map #(string/split % #"\s+")))
    (string/split (read-file "/etc/hosts") #"\n"))
  ,)
