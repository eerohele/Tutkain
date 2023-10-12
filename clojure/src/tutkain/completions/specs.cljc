(ns tutkain.completions.specs
  (:require
   [clojure.spec.alpha :as spec]
   [clojure.test.check.generators :as gen]))

(spec/def ::candidate string?)

(spec/def ::type
  #{:keyword
    :var
    :function
    :static-method
    :macro
    :special-form
    :namespace
    :class
    :method
    :multimethod
    :field
    :navigation})

(spec/def ::completion
  (spec/keys :req-un [::candidate ::type]))

(spec/def ::completions
  (spec/coll-of ::completion :kind sequential? :distinct true :min-count 1))

(spec/def ::arglists (spec/coll-of string?))
(spec/def ::return-type string?)
(spec/def ::doc string?)

(spec/def ::symbol-completion
  (spec/merge ::completion (spec/keys :opt-un [::arglists ::doc])))

(spec/def ::symbol-completions
  (spec/coll-of ::symbol-completion :kind sequential? :min-count 1))

(spec/def ::function-completion
  (spec/keys :req-un [::candidate ::type ::arglists] :opt-un [::doc]))

(spec/def ::function-completions
  (spec/coll-of ::function-completion :kind sequential? :min-count 1))

(spec/def ::method-completion
  (spec/keys :req-un [::candidate ::type ::return-type ::arglists]))

(spec/def ::method-completions
  (spec/coll-of ::method-completion :kind sequential? :min-count 1))

(spec/def ::prefix
  (spec/with-gen string? (constantly (gen/fmap str gen/symbol))))

(spec/def ::ns
  (spec/with-gen #?(:bb any? :clj (partial instance? clojure.lang.Namespace)) #(gen/elements (all-ns))))

(spec/def ::class-completion
  #(= (:type %) :class))

(spec/def ::nested-class-completion
  (spec/and #(= (:type %) :class) #(.contains (:candidate %) "$")))

(defn prefixed-candidates
  [spec prefix]
  (spec/and spec
    (fn [candidates]
      (every? #(.startsWith ^String (:candidate %) prefix) candidates))))
