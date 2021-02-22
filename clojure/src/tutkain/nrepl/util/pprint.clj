(ns tutkain.nrepl.util.pprint
  (:require
   [clojure.pprint :as pprint]))

(defn useless?
  [entry]
  (let [^String s (-> entry first str)]
    (or
      (.startsWith s "nrepl.")
      (.startsWith s "clojure.lang.AFn")
      (.startsWith s "clojure.lang.RestFn"))))

(defn humanize-exception
  [ex]
  (update (Throwable->map ex) :trace (partial remove useless?)))

(defn pprint
  [value writer _]
  (pprint/pprint
    (if (instance? Throwable value) (humanize-exception value) value)
    writer))
