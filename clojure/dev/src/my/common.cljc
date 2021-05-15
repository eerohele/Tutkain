(ns my.common)

(defn parse-int
  [x]
  #?(:clj (Integer/parseInt x)
     :cljs (js/parseInt x)))

(comment
  (parse-int "42")
  )

