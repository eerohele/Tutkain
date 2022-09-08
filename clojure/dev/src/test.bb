(ns ❤️.babashka
  (:require [babashka.fs :as fs])
  (:import (java.time LocalDate)))

;; docstrings
(map str (fs/glob "." "**{.clj,.cljc,.cljs}"))

;; pretty-print results
(into (sorted-map)
  (zipmap (map (comp keyword str char) (range 97 123))
    (range 1 26)))

;; stdout not highlighted
(println "{:a 1}")

;; red stderr
(throw (ex-info "Boom!" {:foo :bar}))

;; auto-complete Java methods

