(ns tutkain.completions
  "Query the Clojure runtime for information on vars, keywords, Java classes,
  etc., presumably for editor auto-completion support.

  Originally adapted from nrepl.util.completion."
  (:require
   [tutkain.backchannel :refer [handle respond-to]]
   [tutkain.java :as java])
  (:import
   (clojure.lang Reflector)
   (java.util.jar JarFile)
   (java.io File)
   (java.lang.reflect Field Member Method Modifier)
   (java.util.jar JarEntry)
   (java.util.concurrent ConcurrentHashMap)))

#_(set! *warn-on-reflection* true)

(when (nil? (System/getProperty "apple.awt.UIElement"))
  (System/setProperty "apple.awt.UIElement" "true"))

(defn annotate-keyword
  [kw]
  {:candidate kw :type :keyword})

(defn all-keywords
  "Return every interned keyword in the Clojure runtime."
  []
  (let [^Field field (.getDeclaredField clojure.lang.Keyword "table")]
    (.setAccessible field true)
    (map keyword (.keySet ^ConcurrentHashMap (.get field nil)))))

(comment (all-keywords),)

(defn qualified-auto-resolved-keywords
  "Given a list of keywords and a map of ns aliases to nses, return all
  available qualified auto-resolved keyword candidates in those namespaces."
  [keywords aliases]
  (mapcat (fn [[ns-alias ns]]
            (eduction
              (filter #(= (namespace %) (str ns)))
              (map #(str "::" ns-alias "/" (name %)))
              keywords))
    aliases))

(comment (qualified-auto-resolved-keywords (all-keywords) (ns-aliases 'clojure.main)),)

(defn unqualified-auto-resolved-keywords
  "Given a list of keywords and an ns symbol, return all unqualified
  auto-resolved keywords in the context of that namespace."
  [keywords ns]
  (eduction
    (filter #(= (namespace %) (str ns)))
    (map #(str "::" (name %)))
    keywords))

(comment (unqualified-auto-resolved-keywords (all-keywords) 'clojure.main),)

(defn keyword-namespace-aliases
  "Given a map of ns alias to ns, return a list of keyword namespace alias
  candidates."
  [aliases]
  (map (comp #(str "::" %) name first) aliases))

(comment (keyword-namespace-aliases (ns-aliases 'clojure.main)),)

(defn simple-keywords
  "Given a list of keywords, return a list of simple keyword candidates."
  [keywords]
  (map str keywords))

(comment (simple-keywords (all-keywords)),)

(defn keyword-candidates
  "Given a list of keywords, a map of ns alias to ns symbol, and a context
  ns, return the keyword candidates available in that context."
  [keywords aliases ns]
  (map annotate-keyword
    (lazy-cat
      (qualified-auto-resolved-keywords keywords aliases)
      (unqualified-auto-resolved-keywords keywords ns)
      (keyword-namespace-aliases aliases)
      (simple-keywords keywords))))

(comment
  (keyword-candidates (all-keywords) (ns-aliases 'clojure.main) 'clojure.main)
  )

(defn namespaces
  "Given an ns symbol, return a list of ns and ns alias symbols available in
  the context of that ns."
  [ns]
  (concat (map ns-name (all-ns)) (keys (ns-aliases ns))))

(comment (namespaces 'clojure.main),)

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
        (filter #(.endsWith ^String (.getName %) ".jar"))
        (mapcat #(-> % .getPath path-files)))
      (-> path File. .getParent File. .listFiles))

    (.endsWith path ".jar")
    (try
      (map (memfn ^JarEntry getName)
        (-> path JarFile. .entries enumeration-seq))
      (catch Exception _))

    :else
    (map #(.replace ^String (.getPath %) path "") (-> path File. file-seq))))

(def non-base-class-names
  "A future that holds a sorted list of the names of all non-base Java classes
  in the class path."
  (->>
    ["sun.boot.class.path" "java.ext.dirs" "java.class.path"]
    (eduction
      (keep #(some-> ^String % System/getProperty (.split File/pathSeparator)))
      cat
      (mapcat path-files)
      (filter #(and (.endsWith ^String % ".class") (not (.contains ^String % "__"))))
      (remove #(re-find #".+\$\d.*" %))
      (map #(.. % (replace ".class" "") (replace "/" "."))))
    future))

(def ^:private base-class-names
  "A future that, on JDK11 and newer, holds a sorted list of all classes in
  every Java module in the current JDK.

  On < JDK11, holds nil."
  (future
    (try
      (when-some [module-finder (Class/forName "java.lang.module.ModuleFinder")]
        (->>
          (Reflector/invokeStaticMethod module-finder "ofSystem" (into-array Object []))
          .findAll
          (eduction
            (mapcat #(-> % .open .list .iterator iterator-seq))
            ;; Remove anonymous nested classes
            (remove #(re-find #".+\$\d.+\.class" %))
            (map #(.. % (replace ".class" "") (replace "/" "."))))))
      (catch ClassNotFoundException _))))

(def ^:private all-class-names
  (future (sort (concat @base-class-names @non-base-class-names))))

(def ^:private top-level-class-names
  (future
    (eduction
      (remove #(.contains ^String % "$"))
      (map annotate-class)
      @all-class-names)))

(def ^:private nested-class-names
  (future
    (eduction
      (filter #(.contains ^String % "$"))
      (map annotate-class)
      @all-class-names)))

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
  (map #(let [doc (some-> % find-ns meta :doc)]
          (cond-> (annotate-namespace %)
            doc (assoc :doc doc)))
    (namespaces ns)))

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
                       (when-let [ns (or (find-ns scope) (scope (ns-aliases ns)))]
                         (ns-public-var-candidates ns)))]
      (map (fn [candidate] (update candidate :candidate #(str scope "/" %))) candidates))))

(defn candidate?
  "Given a string prefix and a candidate map, return true if the candidate
  starts with the prefix."
  [^String prefix {:keys [^String candidate]}]
  (.startsWith candidate prefix))

(defn top-level-class-candidates
  [^String prefix]
  (eduction
    ;; The class candidate list is long and sorted, so instead of filtering
    ;; the entire list, we drop until we get the first candidate, then take
    ;; until the first class that's not a candidate.
    (drop-while (complement (partial candidate? prefix)))
    (take-while (partial candidate? prefix))
    @top-level-class-names))

(comment
  (seq (top-level-class-candidates "clojure.lang"))
  (seq (top-level-class-candidates "java.time"))
  ,)

(defn nested-class-candidates
  [^String prefix]
  (eduction
    (drop-while (complement (partial candidate? prefix)))
    (take-while (partial candidate? prefix))
    @nested-class-names))

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
      (.startsWith prefix ":")
      (candidates-for-prefix prefix (keyword-candidates (all-keywords) (ns-aliases ns) ns))

      (.startsWith prefix ".")
      (candidates-for-prefix prefix (ns-java-method-candidates ns))

      (scoped? prefix)
      (candidates-for-prefix prefix (scoped-candidates prefix ns))

      (and (.contains prefix ".") (.contains prefix "$"))
      (nested-class-candidates prefix)

      (.contains prefix ".")
      (concat
        (candidates-for-prefix prefix (ns-candidates ns))
        (top-level-class-candidates prefix))

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

(defmethod completions :clj
  [{:keys [prefix ns] :as message}]
  (let [ns (or (some-> ns symbol find-ns) (the-ns 'user))]
    (respond-to message {:completions (candidates prefix ns)})))

(defmethod handle :completions
  [message]
  (completions message))
