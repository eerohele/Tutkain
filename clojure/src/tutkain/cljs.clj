(ns tutkain.cljs
  (:refer-clojure :exclude [ns-aliases])
  (:require
   [clojure.string :as string]
   [cljs.analyzer :as analyzer]
   [cljs.analyzer.api :as analyzer.api]
   [cljs.repl :as repl]
   [tutkain.completions :as completions]
   [tutkain.lookup :as lookup]
   [tutkain.repl :refer [handle respond-to]])
  (:import
   (clojure.lang ExceptionInfo)))

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
  [env]
  (into language-keywords
    (filter keyword?)
    (keys (::analyzer/constant-table @env))))

(defn ns-candidates
  [env]
  (map completions/annotate-namespace (analyzer.api/all-ns env)))

(defn ^:private ns-aliases
  [env ns]
  (:requires (analyzer.api/find-ns env ns)))

(defn ns-alias-candidates
  [env ns]
  (map completions/annotate-namespace (map first (ns-aliases env ns))))

(defn ^:private ns-alias->ns-sym
  [env ns alias]
  (get (ns-aliases env ns) alias))

(defn ^:private var-type
  [{:keys [macro fn-var tag] :as x}]
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
  [env ^String prefix ns]
  (when-some [alias (some-> prefix (.split "/") first symbol)]
    (map (fn [v] (update (annotate-var v) :candidate #(str alias "/" %)))
      (remove :private (vals (some->> (ns-alias->ns-sym env ns alias) (analyzer.api/ns-interns env)))))))

(defn ^:private core-candidates
  [env]
  (sequence
    (comp
      (map val)
      (remove :private)
      (map annotate-var))
    (analyzer.api/ns-interns env 'cljs.core)))

(defn ^:private local-candidates
  [env ns]
  (sequence
    (comp
      (map val)
      (map annotate-var))
    (analyzer.api/ns-interns env ns)))

(defn ^:private keyword-candidates
  [env ns]
  (completions/keyword-candidates
    (all-keywords env)
    (into {} (remove #(= (key %) (val %)) (ns-aliases env ns)))
    ns))

(defn candidates
  [env ^String prefix ns]
  (assert (symbol? ns))
  (let [candidates (cond
                     (.startsWith prefix ":") (keyword-candidates env ns)
                     (completions/scoped? prefix) (scoped-candidates env prefix ns)
                     (.contains prefix ".") (ns-candidates env)
                     :else (concat (local-candidates env ns) (core-candidates env) (ns-alias-candidates env ns)))]
    (sort-by :candidate (filter #(completions/candidate? prefix %) candidates))))

(defn ^:private no-shadow?
  [ex]
  ;; For now, fail silently if the error is that the shadow-cljs watch
  ;; isn't running.
  (string/starts-with? (some-> ex Throwable->map :via first :at first name)
    "shadow.cljs.devtools.server.runtime"))

(defn ^:private parse-ns
  [ns]
  (or (some-> ns symbol) 'cljs.user))

(defmethod completions/completions :cljs
  [{:keys [ns prefix build-id] :as message}]
  (try
    (let [completions (candidates (compiler-env build-id) prefix (parse-ns ns))]
      (respond-to message {:completions completions}))
    (catch ExceptionInfo ex
      (if (no-shadow? ex)
        (respond-to message {:completions []})
        (throw ex)))))

(comment
  (candidates (compiler-env :app) "c" 'cljs.core)
  (candidates (compiler-env :app) "string/" 'cljs.pprint)
  (candidates (compiler-env :app) "string/b" 'cljs.pprint)
  (candidates (compiler-env :app) "make-hi" 'cljs.core)
  (candidates (compiler-env :app) ":a" 'cljs.core)
  ,)

(defn special-sym-meta
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
  [env named ns]
  (let [{:keys [arglists file] :as ret} (sym-meta env ns named)]
    (cond-> (select-keys ret [:arglists :doc :file :line :column :name])
      arglists (assoc :arglists (format-arglists arglists))
      file (assoc :file (lookup/resolve-file file)))))

(defmethod lookup/info :cljs
  [{:keys [^String named ns build-id] :as message}]
  (try
    (let [env (compiler-env build-id)
          named (symbol named)]
      (respond-to message {:info (info env named (parse-ns ns))}))
    (catch ExceptionInfo ex
      (if (no-shadow? ex)
        (respond-to message {:info nil})
        (throw ex)))))

(defmethod handle :initialize-cljs
  [message]
  (if-some [get-build-ids (resolve 'shadow.cljs.devtools.api/get-build-ids)]
    (respond-to message {:shadow/build-ids (sort (get-build-ids))})
    (respond-to message {:status :ok})))
