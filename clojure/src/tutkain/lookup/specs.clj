(ns tutkain.lookup.specs
  (:require
   [clojure.spec.alpha :as spec]))

(spec/def ::ns string?)
(spec/def ::name (spec/or :sym symbol? :keyword keyword?))
(spec/def ::file string?)
(spec/def ::column int?)
(spec/def ::line int?)
(spec/def ::arglists (spec/coll-of string?))
(spec/def ::doc string?)
(spec/def ::args string?)
(spec/def ::ret string?)
(spec/def ::fn string?)
(spec/def ::spec string?)

(spec/def ::fnspec
  (spec/keys :opt-un [::args ::ret ::fn]))

(spec/def ::info
  (spec/keys
    :req-un [::name]
    :opt-un [::ns ::file ::column ::line ::arglists ::doc ::fnspec ::spec]))

(spec/def ::infos
  (spec/coll-of ::info :min-count 1 :distinct true))
