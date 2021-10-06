(require '[babashka.fs :as fs])

(map str (fs/glob "." "**{.clj,.cljc,.cljs}"))

;; FIXME
(println "{:a 1}")
