(ns tutkain.nrepl.util.pprint
  (:require
   [tutkain.fipp.v0v6v23.fipp.edn :as fipp]))

(defn useless?
  [entry]
  (let [^String s (-> entry first str)]
    (or
      (.startsWith s "tutkain.")
      (.startsWith s "nrepl.")
      (.startsWith s "clojure.lang.AFn")
      (.startsWith s "clojure.lang.RestFn"))))

(defn humanize-exception
  [ex]
  (update (Throwable->map ex) :trace (partial remove useless?)))

(defn pprint
  [value writer options]
  (fipp/pprint
    (if (instance? Throwable value) (humanize-exception value) value)
    (assoc options :writer writer)))
