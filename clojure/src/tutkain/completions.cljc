(ns tutkain.completions
  "Query the Clojure runtime for information on vars, keywords, Java classes,
  etc., presumably for editor auto-completion support.

  Originally adapted from nrepl.util.completion."
  (:require
   [tutkain.rpc :as rpc :refer [handle respond-to]]
   [tutkain.java :as java])
  (:import
   (java.io File)
   (java.lang.reflect Field Member Method Modifier)
   (java.util.jar JarEntry JarFile)))

(when (nil? (System/getProperty "apple.awt.UIElement"))
  (System/setProperty "apple.awt.UIElement" "true"))

(defn annotate-keyword
  [kw]
  {:candidate kw :type :keyword})

(defn annotate-navigation
  [candidate]
  {:candidate (name candidate) :type :navigation})

(defn all-keywords
  "Return every interned keyword in the Clojure runtime."
  []
  #?(:bb [] ; TODO
     :clj (let [field (.getDeclaredField clojure.lang.Keyword "table")]
            (.setAccessible field true)
            (map keyword (.keySet ^java.util.concurrent.ConcurrentHashMap (.get field nil))))))

(comment (all-keywords),)

(defn qualified-auto-resolved-keyword-candidates
  "Given a list of keywords and a map of ns alias to ns, return all qualified
  auto-resolved keyword candidates in all namespaces in that alias map."
  [keywords aliases]
  (mapcat (fn [[ns-alias ns]]
            (eduction
              (filter #(= (namespace %) (str ns)))
              (map #(str "::" ns-alias "/" (name %)))
              (map annotate-keyword)
              keywords))
    aliases))

(comment (qualified-auto-resolved-keyword-candidates (all-keywords) (ns-aliases 'clojure.main)),)

(defn scoped-auto-resolved-keyword-candidates
  "Given a list of keywords, a list of namespace aliases, and an auto-completion
  prefix like ::foo/, return a list of keyword candidates whose namespace is
  the namespace the alias foo resolves to."
  [keywords aliases ^String prefix]
  (let [prefix-ns-alias (symbol (subs prefix 2 (-> prefix count dec)))
        prefix-ns (str (get aliases prefix-ns-alias))]
    (eduction
      (filter qualified-keyword?)
      (filter #(= (namespace %) prefix-ns))
      (map #(str prefix (name %)))
      (map annotate-keyword)
      keywords)))

(comment (scoped-auto-resolved-keyword-candidates (all-keywords) (ns-aliases 'clojure.spec.alpha) "::c/") ,,,)

(defn scoped-qualified-keyword-candidates
  "Given a list of keywords and an auto-completion prefix like :clojure.core/,
  return a list of keyword candidates whose namespace is the namespace in the
  prefix (e.g. clojure.core)."
  [keywords prefix]
  (let [prefix-ns (subs prefix 1 (-> prefix count dec))]
    (eduction
      (filter qualified-keyword?)
      (filter #(= (namespace %) prefix-ns))
      (map str)
      (map annotate-keyword)
      keywords)))

(comment (scoped-qualified-keyword-candidates (all-keywords) ":clojure.core/") ,,,)

(defn qualified-keyword-candidates
  "Given a list of keywords, return all qualified keyword candidates in that
  list of keywords."
  [keywords]
  (eduction
    (filter qualified-keyword?)
    (map str)
    (map annotate-keyword)
    keywords))

(comment (qualified-keyword-candidates (all-keywords)) ,,,)

(defn unqualified-auto-resolved-keywords
  "Given a list of keywords and an ns symbol, return all auto-resolved keywords
  in that namespace."
  [keywords ns]
  (eduction
    (filter #(= (namespace %) (str ns)))
    (map #(str "::" (name %)))
    keywords))

(comment (unqualified-auto-resolved-keywords (all-keywords) 'clojure.main),)

(defn keyword-namespace-aliases
  "Given a list of keywords and a map of ns alias to ns, return a list of
  keyword namespace alias candidates.

  Only returns keyword namespace aliases that are a part of an interned
  keyword."
  [keywords aliases]
  (let [keyword-nses (into #{}
                       (comp
                         (filter qualified-keyword?)
                         (map (comp symbol namespace)))
                       keywords)]
    (eduction
      (filter (fn [[_ ns]]
                ;; ns-name for ClojureScript compatibility
                (let [ns (if (symbol? ns) ns (ns-name ns))]
                  (contains? keyword-nses ns))))
      (map (fn [[alias _]] (str "::" (name alias))))
      aliases)))

(comment (keyword-namespace-aliases (all-keywords) (ns-aliases 'clojure.main)),)

(defn auto-resolved-keyword-candidates
  "Given a list of keywords, a map of ns alias to ns symbol, and a context ns,
  return the auto-resolved keyword candidates available in that namespace."
  [keywords aliases ns]
  (concat
    (map annotate-keyword (unqualified-auto-resolved-keywords keywords ns))
    (map annotate-navigation (keyword-namespace-aliases keywords aliases))))

(comment
  (auto-resolved-keyword-candidates (all-keywords) (ns-aliases 'clojure.main) 'clojure.main)
  )

(defn keyword-namespaces
  "Given a list of keywords, return a list of the namespaces of all qualified
  keywords in the list."
  [keywords]
  (eduction
    (filter qualified-keyword?)
    (map namespace)
    (distinct)
    (map #(str ":" %))
    keywords))

(comment (keyword-namespaces (all-keywords)) ,,,)

(defn simple-keywords
  "Given a list of keywords, return a list of simple keyword candidates."
  [keywords]
  (eduction
    (filter simple-keyword?)
    (map str)
    keywords))

(comment (simple-keywords (all-keywords)),)

(defn keyword-candidates
  "Given a list of keywords, return a list of simple keyword and keyword
  namespace completion candidates."
  [keywords]
  (concat
    (map annotate-keyword (simple-keywords keywords))
    (map annotate-navigation (keyword-namespaces keywords))))

(comment (keyword-candidates (all-keywords)) ,,,)

(defn namespaces
  "Return a sequence of symbols naming all namespaces loaded into the runtime."
  []
  (map ns-name (all-ns)))

(comment (namespaces) ,,,)

(defn namespace-aliases
  [ns]
  (keys (ns-aliases ns)))

(comment (namespace-aliases 'clojure.main) ,,,)

(defn- static?
  "Given a member of a class, return true if it is a static member."
  [^Member member]
  (-> member .getModifiers Modifier/isStatic))

(defn ns-java-method-candidates
  "Given an ns symbol, return all Java methods that are available in the
  context of that ns."
  [ns]
  (eduction
    (map val)
    (mapcat #(.getMethods ^Class %))
    (map (fn [^Method method]
           {:class (-> method .getDeclaringClass java/qualified-class-name)
            :candidate (str "." (.getName method))
            :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes method))
            :return-type (-> method .getReturnType java/qualified-class-name)
            :type :method}))
    (distinct)
    (ns-imports ns)))

(comment (seq (ns-java-method-candidates 'clojure.main)))

(defn field-candidates
  "Given a java.lang.Class instance, return all field candidates of that class."
  [^Class class]
  (eduction
    (filter static?)
    (map #(hash-map :candidate (.getName ^Field %) :type :field))
    (.getDeclaredFields class)))

(comment (field-candidates java.lang.String) ,)

(defn static-member-candidates
  "Given a java.lang.Class instance, return all static member candidates of
  that class."
  [^Class class]
  (eduction
    (filter static?)
    (map (fn [^Method method]
           {:class (java/qualified-class-name class)
            :candidate (.getName method)
            :type :static-method
            :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes method))
            :return-type (-> method .getReturnType java/qualified-class-name)}))
    (.getMethods class)))

(comment (static-member-candidates java.lang.String),)

(defn annotate-class
  [class-name]
  {:candidate (name class-name) :type :class})

(defn annotate-var [var]
  (let [{macro :macro arglists :arglists var-name :name doc :doc} (meta var)
        type (cond macro :macro arglists :function :else :var)]
    (cond-> {:candidate (name var-name) :type type}
      doc (assoc :doc doc)
      arglists (assoc :arglists (map pr-str arglists)))))

(defn path-files
  [^String path]
  (cond
    (.endsWith path "/*")
    (sequence
      (comp
        (filter #(.endsWith ^String (.getName ^File %) ".jar"))
        (mapcat #(-> ^File % .getPath path-files)))
      (-> path File. .getParent File. .listFiles))

    (.endsWith path ".jar")
    (try
      (with-open [jar-file (JarFile. path)]
        (mapv (memfn ^JarEntry getName) (-> jar-file .entries enumeration-seq)))
      (catch Exception _))

    :else
    (map #(.replace ^String (.getPath ^File %) path "") (-> path File. file-seq))))

(defn ^:private non-base-classes
  "Return a sequence of the names of all non-base Java classes in the class
  path."
  []
  #?(:bb []
     :clj (eduction
            (mapcat path-files)
            (filter #(.endsWith ^String % ".class"))
            (remove #(.startsWith ^String % "META-INF/"))
            (remove #(.contains ^String % "__"))
            (remove #(re-find #".+\$\d.*" %))
            (map #(.. ^String % (replace ".class" "") (replace "/" ".")))
            (.split (System/getProperty "java.class.path") File/pathSeparator))))

(defn ^:private base-classes
  "Return a sequence of all java.* and javax.* classes in every Java module in
  the current JDK."
  []
  #?(:bb (map (memfn getName) (babashka.classes/all-classes))
     :clj (let [module-finder (java.lang.module.ModuleFinder/ofSystem)]
            (eduction
              cat
              ;; Remove anonymous nested classes
              (remove #(re-find #".+\$\d.+\.class" %))
              ;; Only retain java.* and javax.* to limit memory consumption
              (map #(.. ^String % (replace ".class" "") (replace "/" ".")))
              (filter #(or (.startsWith ^String % "java.") (.startsWith ^String % "javax.")))
              (for [^java.lang.module.ModuleReference module-reference (.findAll module-finder)]
                (with-open [module-reader (.open module-reference)
                            stream (.list module-reader)]
                  (iterator-seq (.iterator stream))))))))

(def ^:private all-class-candidates
  (future
    (map annotate-class
      (into (sorted-set)
        (concat (non-base-classes) (base-classes))))))

(defn ^:private nested-class-names
  []
  (filter #(.contains ^String (:candidate %) "$")
    @all-class-candidates))

(def special-form-candidates
  "All Clojure special form candidates."
  [{:candidate "def" :ns "clojure.core" :type :special-form}
   {:candidate "do" :ns "clojure.core" :type :special-form}
   {:candidate "dot" :ns "clojure.core" :type :special-form}
   {:candidate "fn" :ns "clojure.core" :type :special-form}
   {:candidate "if" :ns "clojure.core" :type :special-form}
   {:candidate "let" :ns "clojure.core" :type :special-form}
   {:candidate "loop" :ns "clojure.core" :type :special-form}
   {:candidate "monitor-enter" :ns "clojure.core" :type :special-form}
   {:candidate "monitor-exit" :ns "clojure.core" :type :special-form}
   {:candidate "new" :ns "clojure.core" :type :special-form}
   {:candidate "quote" :ns "clojure.core" :type :special-form}
   {:candidate "recur" :ns "clojure.core" :type :special-form}
   {:candidate "set!" :ns "clojure.core" :type :special-form}
   {:candidate "throw" :ns "clojure.core" :type :special-form}
   {:candidate "try" :ns "clojure.core" :type :special-form}
   {:candidate "var" :ns "clojure.core" :type :special-form}])

(defn annotate-namespace
  [ns]
  {:candidate (name ns) :type :namespace})

(defn ns-candidates
  "Given an ns symbol, return all namespace candidates that are available in
  the context of that namespace."
  [ns]
  (concat
    (map (fn [ns]
           (let [doc (some-> ns find-ns meta :doc)]
             (cond-> (annotate-namespace (name ns)) doc (assoc :doc doc))))
      (namespaces))
    (map annotate-navigation (namespace-aliases ns))))

(comment (ns-candidates 'clojure.main),)

(defn ns-var-candidates
  "Given an ns symbol, return all vars that are available in the context of
  that namespace."
  [ns]
  (eduction
    (map val)
    (filter var?)
    (map annotate-var)
    (ns-map ns)))

(defn ns-public-var-candidates
  "Given an ns symbol, return all public var candidates in that namespace."
  [ns]
  (eduction
    (map val)
    (map annotate-var)
    (ns-publics ns)))

(comment (ns-public-var-candidates 'clojure.set),)

(defn ns-class-candidates
  "Given an ns symbol, return all class candidates that are imported into that
  namespace, as well as the possible constructor candidates for each class."
  [ns]
  (eduction
    (map key)
    (map annotate-class)
    (ns-imports ns)))

(comment (ns-class-candidates 'clojure.main),)

(defn scoped?
  "Given a string prefix, return true if it's scoped.

  A prefix is scoped if it contains, but does not start with, a forward slash."
  [^String prefix]
  (and (not (.startsWith prefix "/")) (.contains prefix "/")))

(defn scoped-candidates
  "Given a scoped string prefix (e.g. \"set/un\" for clojure.set/union) and an
  ns symbol, return auto-completion candidates that match the prefix.

  Searches Java static class members and public vars in Clojure namespaces."
  [^String prefix ns]
  (when-let [prefix-scope (first (.split prefix "/"))]
    (let [scope (symbol prefix-scope)
          candidates (if-let [class (java/resolve-class ns scope)]
                       (concat (static-member-candidates class) (field-candidates class))
                       (concat
                         (some-> scope find-ns ns-public-var-candidates)
                         (some-> ns ns-aliases scope ns-public-var-candidates)))]
      (map (fn [candidate] (update candidate :candidate #(str scope "/" %))) candidates))))

(defn candidate?
  "Given a string prefix and a candidate map, return true if the candidate
  starts with the prefix."
  [^String prefix {:keys [^String candidate]}]
  (.startsWith candidate prefix))

(defn class-candidates
  [^String prefix]
  (eduction
    ;; The class candidate list is long and sorted, so instead of filtering
    ;; the entire list, we drop until we get the first candidate, then take
    ;; until the first class that's not a candidate.
    (drop-while (complement (partial candidate? prefix)))
    (take-while (partial candidate? prefix))
    @all-class-candidates))

(comment
  (seq (class-candidates "clojure.lang"))
  (seq (class-candidates "java.time"))
  ,)

(defn nested-class-candidates
  [^String prefix]
  (eduction
    (drop-while (complement (partial candidate? prefix)))
    (take-while (partial candidate? prefix))
    (nested-class-names)))

(comment (seq (nested-class-candidates "java.util.Spliterator")) ,)

(defn ^:private candidates-for-prefix
  [prefix candidates]
  (sort-by :candidate (filter #(candidate? prefix %) candidates)))

(defn candidates
  "Given a string prefix and ns symbol, return auto-completion candidates for
  the string prefix.

  See the comment form below for examples."
  [^String prefix ns]
  (when (seq prefix)
    (cond
      (and (.startsWith prefix "::") (.endsWith prefix "/"))
      (candidates-for-prefix prefix (scoped-auto-resolved-keyword-candidates (all-keywords) (ns-aliases ns) prefix))

      (and (.startsWith prefix "::") (.contains prefix "/"))
      (candidates-for-prefix prefix (qualified-auto-resolved-keyword-candidates (all-keywords) (ns-aliases ns)))

      (and (.startsWith prefix ":") (.endsWith prefix "/"))
      (candidates-for-prefix prefix (scoped-qualified-keyword-candidates (all-keywords) prefix))

      (and (.startsWith prefix ":") (.contains prefix "/"))
      (candidates-for-prefix prefix (qualified-keyword-candidates (all-keywords)))

      (.startsWith prefix "::")
      (candidates-for-prefix prefix (auto-resolved-keyword-candidates (all-keywords) (ns-aliases ns) ns))

      (.startsWith prefix ":")
      (candidates-for-prefix prefix (keyword-candidates (all-keywords)))

      (.startsWith prefix ".")
      (candidates-for-prefix prefix (ns-java-method-candidates ns))

      (scoped? prefix)
      (candidates-for-prefix prefix (scoped-candidates prefix ns))

      (and (.contains prefix ".") (.contains prefix "$"))
      (nested-class-candidates prefix)

      (.contains prefix ".")
      (concat
        (candidates-for-prefix prefix (ns-candidates ns))
        (class-candidates prefix))

      :else
      (candidates-for-prefix prefix
        (concat special-form-candidates
          (ns-candidates ns)
          (ns-var-candidates ns)
          (ns-class-candidates ns))))))

(comment
  (candidates "ran" 'clojure.core)
  (candidates "Strin" 'clojure.core)
  (candidates "Throwable" 'clojure.core)

  (time (dorun (candidates "m" 'clojure.core)))
  (time (dorun (candidates "java." *ns*)))
  (time (dorun (candidates "java" *ns*)))

  (require '[clj-async-profiler.core :as prof])
  (prof/profile (dorun (candidates "java." *ns*)))
  (prof/serve-files 1337)
  ,)

(defmulti completions :dialect)

(defmethod completions :default
  [{:keys [prefix] :as message}]
  (respond-to message {:completions (candidates prefix (rpc/namespace message))}))

(defmethod handle :completions
  [message]
  (completions message))
