(ns tutkain.cljs
  (:refer-clojure :exclude [ns-aliases])
  (:require
   [cljs.analyzer :as analyzer]
   [cljs.analyzer.api :as analyzer.api]
   [cljs.repl :as repl]
   [tutkain.completions :as completions]
   [tutkain.lookup :as lookup]
   [tutkain.backchannel :refer [handle respond-to]]))

(set! *warn-on-reflection* true)

(def ^:dynamic *compiler-env*
  (atom {}))

(defn ^:private format-arglists
  [arglists]
  ;; Why?
  (map pr-str (if (= 'quote (first arglists)) (rest arglists) arglists)))

(defn ^:private shadow-compiler-env
  [build-id]
  (when-some [f (resolve 'shadow.cljs.devtools.api/compiler-env)]
    (atom (f build-id))))

#_(defn ^:private figwheel-compiler-env
  [build-id]
  (some->
    (resolve 'figwheel.main/build-registry)
    deref
    deref
    ;; FIXME: build-id
    (get-in ["dev" :repl-options :compiler-env])))

(defn compiler-env
  ([]
   (or *compiler-env* (analyzer.api/current-state)))
  ([build-id]
   (or (shadow-compiler-env build-id) (compiler-env))))

;; Stolen from Suitable
(def ^:private language-keywords
  #{:require :require-macros :import
    :refer :refer-macros :include-macros
    :refer-clojure :exclude
    :keys :strs :syms
    :as :or
    :pre :post
    :let :when :while

    ;; reader conditionals
    :clj :cljs :default

    ;; common meta keywords
    :private :tag :static
    :doc :author :arglists
    :added :const

    ;; spec keywords
    :req :req-un :opt :opt-un
    :args :ret :fn

    ;; misc
    :keywordize-keys :else :gen-class})

(defn all-keywords
  "Given a compiler environment, return a list of all of the keywords the
  compiler knows about."
  [env]
  (into language-keywords
    (filter keyword?)
    (keys (::analyzer/constant-table @env))))

(defn ns-candidates
  "Given a compiler environment, return all namespace auto-completion
  candidates."
  [env]
  (map completions/annotate-namespace (analyzer.api/all-ns env)))

(defn ^:private ns-aliases
  [env ns]
  (:requires (analyzer.api/find-ns env ns)))

(defn ns-alias-candidates
  "Given a compiler environment and an ns symbol, return all namespace alias
  auto-completion candidates available in the given namespace."
  [env ns]
  (map completions/annotate-namespace (map first (ns-aliases env ns))))

(defn ^:private ns-alias->ns-sym
  [env ns alias]
  (get (ns-aliases env ns) alias))

(defn ^:private var-type
  [{:keys [macro fn-var tag]}]
  (cond
    (= tag 'cljs.core/MultiFn) :multimethod
    macro :macro
    fn-var :function
    :else :var))

(defn ^:private annotate-var
  [{arglists :arglists doc :doc var-name :name :as v}]
  (cond-> {:candidate (name var-name)
           :type (var-type v)}
    (seq arglists) (assoc :arglists (format-arglists arglists))
    (seq doc) (assoc :doc doc)))

(defn scoped-candidates
  "Given a compiler environment, a string prefix, and an ns symbol, return all
  scoped candidates that match the given prefix."
  [env ^String prefix ns]
  (when-some [alias (some-> prefix (.split "/") first symbol)]
    (sequence
      (comp
        (map val)
        (remove :private)
        (map (fn [v] (update (annotate-var v) :candidate #(str alias "/" %)))))
      (some->> (ns-alias->ns-sym env ns alias) (analyzer.api/ns-interns env)))))

(defn ^:private core-candidates
  "Given a compiler environment, return all auto-completion candidates in
  cljs.core."
  [env]
  (sequence
    (comp
      (map val)
      (remove :private)
      (map annotate-var))
    (analyzer.api/ns-interns env 'cljs.core)))

(defn ^:private ns-var-candidates
  "Given a compiler environment and an ns symbol, return all var
  auto-completion candidates in the namespace."
  [env ns]
  (sequence
    (comp
      (map val)
      (map annotate-var))
    (analyzer.api/ns-interns env ns)))

(defn ^:private keyword-candidates
  "Given a compiler environment and an ns symbol, return all keyword
  auto-completion candidates in the context of the namespace."
  [env ns]
  (completions/keyword-candidates
    (all-keywords env)
    (into {} (remove #(= (key %) (val %)) (ns-aliases env ns)))
    ns))

(defn candidates
  "Given a compiler environment, a string prefix, and an ns symbol, return all
  applicable auto-completion candidates for the prefix."
  [env ^String prefix ns]
  (assert (symbol? ns))
  (let [candidates (cond
                     (.startsWith prefix ":") (keyword-candidates env ns)
                     (completions/scoped? prefix) (scoped-candidates env prefix ns)
                     (.contains prefix ".") (ns-candidates env)
                     :else (concat (ns-var-candidates env ns) (core-candidates env) (ns-alias-candidates env ns)))]
    (sort-by :candidate (filter #(completions/candidate? prefix %) candidates))))

(defn ^:private parse-ns
  [ns]
  (or (some-> ns symbol) 'cljs.user))

(defmethod handle :completions
  [{:keys [ns prefix build-id] :as message}]
  (let [completions (candidates (compiler-env build-id) prefix (parse-ns ns))]
    (respond-to message {:completions completions})))

(comment
  (candidates (compiler-env :browser) "c" 'cljs.core)
  (candidates (compiler-env :browser) "string/" 'cljs.pprint)
  (candidates (compiler-env :browser) "string/b" 'cljs.pprint)
  (candidates (compiler-env :browser) "make-hi" 'cljs.core)
  (candidates (compiler-env :browser) ":a" 'cljs.core)
  ,)

(defn special-sym-meta
  "Given a symbol that names a ClojureScript special form, return metadata for
  that special form."
  [sym]
  (when-some [{:keys [doc forms]} (get repl/special-doc-map sym)]
    {:name (symbol "cljs.core" (str sym))
     :doc doc
     :arglists forms
     :file "cljs/core.cljs"}))

(defn ^:private core-sym-meta
  [env sym]
  (get (analyzer.api/ns-interns env 'cljs.core) sym))

(defn ^:private ns-sym-meta
  [env ns sym]
  (get (analyzer.api/ns-interns env ns) sym))

(defn ^:private qualified-sym-meta
  [env ns ns-alias sym]
  (get (some->> (ns-alias->ns-sym env ns ns-alias) (analyzer.api/ns-interns env)) sym))

(defn ^:private sym-meta
  [env ns named]
  (let [sym (symbol (name named))]
    (if (qualified-symbol? named)
      (qualified-sym-meta env ns (symbol (namespace named)) sym)
      (or (special-sym-meta sym) (core-sym-meta env sym) (ns-sym-meta env ns sym)))))

(defn info
  "Given a compiler environment, a symbol that names a clojure.lang.Named
  instance, and an ns symbol, return selected metadata for the named var."
  [env named ns]
  (let [{:keys [arglists file] :as ret} (sym-meta env ns named)]
    (cond-> (select-keys ret [:arglists :doc :file :line :column :name])
      arglists (assoc :arglists (format-arglists arglists))
      file (assoc :file (lookup/resolve-file file)))))

(defmethod handle :lookup
  [{:keys [^String named ns build-id] :as message}]
  (let [env (compiler-env build-id)
        named (symbol named)]
    (respond-to message {:info (info env named (parse-ns ns))})))
