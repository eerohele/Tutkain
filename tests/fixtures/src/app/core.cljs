(ns app.core)

(defn parse-int
  [x]
  (js/parseInt x 10))

(comment
  (parse-int "42")
  )
