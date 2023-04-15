(ns tutkain.query
  (:refer-clojure :exclude [loaded-libs])
  (:require
   [clojure.core :as core]
   [clojure.xml :as xml]
   [tutkain.rpc :refer [handle respond-to]]
   [tutkain.lookup :as lookup])
  (:import (java.net URI URLEncoder)
           (java.net.http HttpClient HttpRequest HttpResponse$BodyHandlers)))

(defn ^:private meta-with-type
  [var]
  (when (var? var)
    (let [{:keys [macro arglists] :as m} (meta var)
          v (var-get var)]
      (assoc m :type (cond
                       (= clojure.lang.MultiFn (class v)) :multimethod
                       (and (map? v) (contains? v :impls)) :protocol
                       macro :macro
                       arglists :function
                       :else :var)))))

(defmethod handle :apropos
  [{:keys [pattern] :as message}]
  (when-some [re (some-> pattern not-empty re-pattern)]
    (let [vars (eduction
                 (map ns-publics)
                 (mapcat vals)
                 (map meta-with-type)
                 (filter (fn [{:keys [doc name]}]
                           (or
                             (and doc (re-find (re-matcher re doc)))
                             (re-find (re-matcher re (str name))))))
                 (map lookup/prep-meta)
                 (all-ns))]
      (respond-to message {:results (sort-by (juxt :ns :name) vars)}))))

(defmethod handle :dir
  [{:keys [ns sym] :as message}]
  (let [sym (symbol sym)
        ns (or (some-> ns symbol find-ns) (the-ns 'user))]
    (when-some [sym-ns (or
                         ;; symbol naming ns
                         (some-> sym symbol find-ns)
                         ;; ns alias symbol
                         (get (ns-aliases ns) sym)
                         ;; non-ns symbol
                         (symbol (namespace (symbol (ns-resolve ns sym)))))]
      (let [vars (eduction
                   (map val)
                   (map meta-with-type)
                   (map lookup/prep-meta)
                   (ns-publics sym-ns))]
        (respond-to message {:symbol sym
                             :results (sort-by :name vars)})))))

(defmulti loaded-libs :dialect)

(defmethod loaded-libs :clj
  [message]
  (let [libs (eduction
               (map lookup/ns-meta)
               (map lookup/prep-meta)
               (filter :file)
               (remove (comp #{"NO_SOURCE_PATH"} :file))
               #?(:bb [] :clj (core/loaded-libs)))]
    (respond-to message {:results libs})))

(defmethod loaded-libs :bb [_])

(defmethod handle :loaded-libs
  [message]
  (loaded-libs message))

(defmulti intern-mappings :dialect)

(defmethod intern-mappings :clj
  [{:keys [ns] :as message}]
  (when-some [ns (some-> ns find-ns)]
    (let [interns (eduction
                    (map val)
                    (map meta-with-type)
                    (map lookup/prep-meta)
                    (ns-interns ns))]
      (respond-to message {:results interns}))))

(defmethod handle :intern-mappings
  [message]
  (intern-mappings message))

(defmulti remove-namespace-mapping :dialect)

(defmethod remove-namespace-mapping :clj
  [{:keys [ns sym] :as message}]
  (try
    (ns-unmap (some-> ns find-ns) sym)
    (respond-to message {:result :ok :ns ns :sym sym})
    (catch Exception _
      (respond-to message {:result :nok}))))

(defmethod handle :remove-namespace-mapping
  [message]
  (remove-namespace-mapping message))

(defmulti alias-mappings :dialect)

(defmethod alias-mappings :clj
  [{:keys [ns] :as message}]
  (when-some [ns (some-> ns find-ns)]
    (let [aliases (map (fn [[alias ns]] {:type :namespace
                                         :doc (-> ns ns-name str)
                                         :name alias})
                    (ns-aliases ns))]
      (respond-to message {:results aliases}))))

(defmethod handle :alias-mappings
  [message]
  (alias-mappings message))

(defmulti remove-namespace-alias :dialect)

(defmethod remove-namespace-alias :clj
  [{:keys [ns sym] :as message}]
  (try
    (ns-unalias (some-> ns find-ns) sym)
    (respond-to message {:result :ok :ns ns :sym sym})
    (catch Exception _
      (respond-to message {:result :nok}))))

(defmethod handle :remove-namespace-alias
  [message]
  (remove-namespace-alias message))

(defmulti all-namespaces :dialect)

(defmethod all-namespaces :clj
  [message]
  (let [ns-metas (sort-by :name
                   (keep (fn [ns]
                           (-> ns ns-name lookup/ns-meta lookup/prep-meta))
                     (all-ns)))]
    (respond-to message {:results ns-metas})))

(defmethod handle :all-namespaces
  [message]
  (all-namespaces message))

(defmulti remove-namespace :dialect)

(defmethod remove-namespace :clj
  [{:keys [ns] :as message}]
  (try
    (some-> ns remove-ns)
    (respond-to message {:result :ok :ns ns})
    (catch Exception _
      (respond-to message {:result :nok}))))

(defmethod handle :remove-namespace
  [message]
  (remove-namespace message))

(defmacro ^:private rapply
  [sym & args]
  `(if-some [f# (requiring-resolve '~sym)]
     (f# ~@args)
     (throw (ex-info "Can't resolve sym" {:sym '~sym}))))

(defmethod handle :sync-deps
  [message]
  (try
    (rapply clojure.repl.deps/sync-deps (select-keys message [:aliases]))
    (respond-to message {:tag :ret :val :ok})
    (catch Exception ex
      (respond-to message {:tag :err :val (.getMessage ex)}))))

(defmethod handle :add-lib
  [{:keys [lib] :as message}]
  (try
    (rapply clojure.repl.deps/add-lib lib)
    (respond-to message {:tag :ret :val :ok})
    (catch Exception ex
      (respond-to message {:tag :err :val (.getMessage ex)}))))

(defmethod handle :add-libs
  [{:keys [lib-coords] :as message}]
  (try
    (rapply clojure.repl.deps/add-libs lib-coords)
    (respond-to message {:tag :ret :val :ok})
    (catch Exception ex
      (respond-to message {:tag :err :val (.getMessage ex)}))))

(defn ^:private http-request
  [uri]
  (let [http-client (HttpClient/newHttpClient)
        body-handler (HttpResponse$BodyHandlers/ofInputStream)
        request-builder (HttpRequest/newBuilder)
        request (.. request-builder (uri uri) (build))
        response (.send http-client request body-handler)]
    (.body response)))

(defmethod handle :find-libs
  [{:keys [repo q max-results]
    :or {max-results 25}
    :as message}]
  (try
    (case repo
      clojars
      (let [uri (URI/create (format "https://clojars.org/search?q=%s&format=xml" (URLEncoder/encode q)))
            response (http-request uri)
            results (into []
                      (comp
                        (take max-results)
                        (map :attrs)
                        (map (fn [{:keys [description group_name jar_name version]}]
                               {:group-id group_name
                                :artifact-id jar_name
                                :version version
                                :description description})))
                      (some-> response xml/parse :content))]
        (respond-to message {:results results}))

      maven
      (let [uri (URI/create (format "https://search.maven.org/solrsearch/select?q=%s&rows=%d&wt=xml" (URLEncoder/encode q) max-results))
            response (http-request uri)
            results (into []
                      (comp
                        (take max-results)
                        (map :content)
                        (map (fn [doc]
                               (let [group-id (-> doc (nth 2) :content first)
                                     artifact-id (-> doc (nth 0) :content first)
                                     version (-> doc (nth 4) :content first)]
                                 {:group-id group-id
                                  :artifact-id artifact-id
                                  :version version}))))
                      (some-> response xml/parse :content second :content))]
        (respond-to message {:results results})))
    (catch Exception ex
      (respond-to message {:tag :err :val (or (.getMessage ex) "Unknown error")}))))
