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
(spec/def ::type #{:function :macro :multimethod :protocol :var :namespace})

(spec/def ::fnspec
  (spec/keys :opt-un [::args ::ret ::fn]))

(spec/def ::info
  (spec/keys
    :req-un [::name ::ns]
    :opt-un [::file ::column ::line ::arglists ::doc ::fnspec ::spec ::type]))

(spec/def ::ns-info
  (spec/keys
    :req-un [::name ::column ::line]
    :opt-un [::file ::doc ::type]))

(spec/def ::spec-info
  (spec/keys :req-un [::name ::spec]))

(spec/def ::infos
  (spec/coll-of (spec/or :info ::info :ns-info ::ns-info) :min-count 1 :distinct true))
