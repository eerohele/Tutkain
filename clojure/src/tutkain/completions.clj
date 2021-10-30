(ns tutkain.completions
  "Query the Clojure runtime for information on vars, keywords, Java classes,
  etc., presumably for editor auto-completion support.

  Originally adapted from nrepl.util.completion."
  (:require
   [clojure.main :as main]
   [tutkain.backchannel :refer [handle respond-to]])
  (:import
   (clojure.lang Reflector)
   (java.util.jar JarFile)
   (java.io File)
   (java.lang.reflect Constructor Field Member Method Modifier)
   (java.util.jar JarEntry)
   (java.util.concurrent ConcurrentHashMap)))

#_(set! *warn-on-reflection* true)

(when (nil? (System/getProperty "apple.awt.UIElement"))
  (System/setProperty "apple.awt.UIElement" "true"))

(defn annotate-keyword
  [kw]
  {:candidate kw :type :keyword})

(defn all-keywords
  "Return the name of every interned keyword in the Clojure runtime."
  []
  (let [^Field field (.getDeclaredField clojure.lang.Keyword "table")]
    (.setAccessible field true)
    (map keyword (.keySet ^ConcurrentHashMap (.get field nil)))))

(comment (all-keywords),)

(defn- resolve-namespace
  [sym aliases]
  (get aliases sym (find-ns sym)))

(defn qualified-auto-resolved-keywords
  "Given a list of keywords and a list of ns aliases, return all available
  qualified auto-resolved keyword candidates."
  [keywords aliases]
  (mapcat (fn [[ns-alias _]]
            (let [ns-alias-name (str (resolve-namespace (symbol ns-alias) aliases))]
              (eduction
                (filter #(= (namespace %) ns-alias-name))
                (map #(str "::" ns-alias "/" (name %)))
                keywords)))
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

(defn ^:private qualified-class-name
  [^Class class]
  (let [class-name (.getSimpleName class)]
    (if-some [package-name (some-> class .getPackage .getName)]
      (str package-name "." class-name)
      class-name)))

(defn ns-java-method-candidates
  "Given an ns symbol, return all Java methods that are available in the
  context of that ns."
  [ns]
  (eduction
    (map val)
    (mapcat #(.getMethods ^Class %))
    (map (fn [^Method method]
           {:class (-> method .getDeclaringClass qualified-class-name)
            :candidate (str "." (.getName method))
            :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes method))
            :return-type (-> method .getReturnType qualified-class-name)
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
           {:class (qualified-class-name class)
            :candidate (.getName method)
            :type :static-method
            :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes method))
            :return-type (-> method .getReturnType qualified-class-name)}))
    (.getMethods class)))

(comment (static-member-candidates java.lang.String),)

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

(def class-files
  (->>
    ["sun.boot.class.path" "java.ext.dirs" "java.class.path"]
    (eduction
      (keep #(some-> ^String % System/getProperty (.split File/pathSeparator)))
      cat
      (mapcat path-files)
      (filter #(and (.endsWith ^String % ".class") (not (.contains ^String % "__")))))
    delay))

(defn- classname [^String file]
  (.. file (replace ".class" "") (replace "/" ".")))

(defn annotate-class
  [class-name]
  {:candidate (name class-name) :type :class})

(def system-module-resources
  "A future that, on JDK11 and newer, holds a seq of all classes in every Java
  module in the current JDK.

  On < JDK11, holds nil."
  (future
    (try
      (when-some [module-finder (Class/forName "java.lang.module.ModuleFinder")]
        (->>
          (Reflector/invokeStaticMethod module-finder "ofSystem" (into-array Object []))
          .findAll
          (eduction
            (mapcat #(-> % .open .list .iterator iterator-seq))
            (map classname))
          sort))
      (catch ClassNotFoundException _))))

(def top-level-classes
  (future
    (sort
      (eduction
        (filter #(re-find #"^[^\$]+\.class" %))
        (map classname)
        @class-files))))

(def nested-classes
  (future
    (sort
      (eduction
        (filter #(re-find #"^[^\$]+(\$[^\d]\w*)+\.class" %))
        (map classname)
        @class-files))))

(defn resolve-class
  "Given an ns symbol and a symbol, if the symbol resolves to a class in the
  context of the given namespace, return that class (java.lang.Class)."
  [ns sym]
  (try (let [val (ns-resolve ns sym)]
         (when (class? val) val))
    (catch Exception e
      (when (not= ClassNotFoundException
              (class (main/repl-exception e)))
        (throw e)))))

(comment (resolve-class 'clojure.core 'String) ,)

(defn annotate-var [var]
  (let [{macro :macro arglists :arglists var-name :name doc :doc} (meta var)
        type (cond macro :macro arglists :function :else :var)]
    (cond-> {:candidate (name var-name) :type type}
      doc (assoc :doc doc)
      arglists (assoc :arglists (map pr-str arglists)))))

(def class-candidate-list
  (delay (concat @system-module-resources @top-level-classes @nested-classes)))

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
    (mapcat
      (fn [class-name]
        (into [(annotate-class class-name)]
          (when-some [^Class class (-> class-name symbol resolve)]
            (map (fn [^Constructor constructor]
                   {:candidate (str class-name ".")
                    :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes constructor))
                    :return-type (qualified-class-name class)
                    :type :method})
              (.getConstructors class))))))
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
          candidates (if-let [class (resolve-class ns scope)]
                       (concat (static-member-candidates class) (field-candidates class))
                       (when-let [ns (or (find-ns scope) (scope (ns-aliases ns)))]
                         (ns-public-var-candidates ns)))]
      (map (fn [candidate] (update candidate :candidate #(str scope "/" %))) candidates))))

(defn candidate?
  "Given a string prefix and a candidate map, return true if the candidate
  starts with the prefix."
  [^String prefix {:keys [^String candidate]}]
  (.startsWith candidate prefix))

(defn class-candidates
  [^String prefix]
  (let [candidate? (partial candidate? prefix)]
    (eduction
      (map annotate-class)
      ;; Ignore nested classes if the prefix does not contain a dollar sign.
      (remove #(and (not (.contains prefix "$")) (.contains ^String (:candidate %) "$")))
      ;; The class candidate list is long and sorted, so instead of filtering
      ;; the entire list, we drop until we get the first candidate, then take
      ;; until the first class that's not a candidate.
      (drop-while (complement candidate?))
      (take-while candidate?)
      (mapcat (fn [{^String class-name :candidate}]
                (into [(annotate-class class-name)]
                  (try
                    (map (fn [^Constructor constructor]
                           {:candidate (str class-name ".")
                            :arglists (try
                                        (mapv (memfn ^Class getSimpleName) (.getParameterTypes constructor))
                                        (catch java.lang.IllegalAccessError _)
                                        (catch java.util.ServiceConfigurationError _))
                            :return-type (or (some-> class-name (.split "\\.") last) "")
                            :type :method})
                      (when-some [^Class class (some-> class-name symbol resolve)]
                        (.getConstructors class)))
                    (catch java.lang.NoClassDefFoundError _)
                    (catch java.lang.IllegalAccessError _)))))
      @class-candidate-list)))

(comment (seq (class-candidates "java.util.concurrent.Linked")) ,)

(defn candidates
  "Given a string prefix and ns symbol, return auto-completion candidates for
  the string prefix.

  See the comment form below for examples."
  [^String prefix ns]
  (when (seq prefix)
    (let [candidates (cond
                       (.startsWith prefix ":") (keyword-candidates (all-keywords) (ns-aliases ns) ns)
                       (.startsWith prefix ".") (ns-java-method-candidates ns)
                       (scoped? prefix) (scoped-candidates prefix ns)
                       (.contains prefix ".") (concat (ns-candidates ns) (class-candidates prefix))
                       :else (concat special-form-candidates
                               (ns-candidates ns)
                               (ns-var-candidates ns)
                               (ns-class-candidates ns)))]
      (sort-by :candidate (filter #(candidate? prefix %) candidates)))))

(comment
  (candidates "ran" 'clojure.core)
  (candidates "Strin" 'clojure.core)
  (candidates "Throwable" 'clojure.core)
  (time (dorun (candidates "m" 'clojure.core)))
  (time (dorun (candidates "java." *ns*)))

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
