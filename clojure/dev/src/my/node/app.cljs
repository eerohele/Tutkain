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
  (def remove-comments (remove #(string/starts-with? % "#")))
  (def split-by-whitespace (map #(string/split % #"\s+")))

  (->>
    (read-file "/etc/hosts")
    (string/split-lines)
    (into (sorted-set)
      (comp remove-comments split-by-whitespace)))
  ,)
