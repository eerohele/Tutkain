(ns tutkain.repl.runtime.completions
  (:require
   [clojure.main :as main]
   [tutkain.repl.runtime.repl :refer [handle response-for]])
  (:import
   (clojure.lang Reflector)
   (java.util.jar JarFile)
   (java.io File)
   (java.lang.reflect Field Member Modifier)
   (java.util.jar JarEntry)
   (java.util.concurrent ConcurrentHashMap)))

;; Adapted from nrepl.util.completion

(defn annotate-keyword
  [kw]
  {:candidate kw :type :keyword})

(defn all-keywords
  []
  (let [^Field field (.getDeclaredField clojure.lang.Keyword "table")]
    (.setAccessible field true)
    (lazy-seq (.keySet ^ConcurrentHashMap (.get field nil)))))

(defn- resolve-namespace
  [sym ns]
  (get (ns-aliases ns) sym (find-ns sym)))

(defn qualified-auto-resolved-keywords
  [keywords ns]
  (mapcat (fn [[ns-alias _]]
            (let [ns-alias-name (str (resolve-namespace (symbol ns-alias) ns))]
              (sequence
                (comp
                  (filter #(= (namespace %) ns-alias-name))
                  (map #(str "::" ns-alias "/" (name %)))
                  (map annotate-keyword))
                keywords)))
    (ns-aliases ns)))

(defn unqualified-auto-resolved-keywords
  [keywords ns]
  (sequence
    (comp
      (filter #(= (namespace %) (str ns)))
      (map #(str "::" (name %)))
      (map annotate-keyword))
    keywords))

(defn keyword-namespace-aliases
  [ns]
  (map (comp annotate-keyword #(str "::" (name %)) name first) (ns-aliases ns)))

(defn single-colon-keywords
  [keywords]
  (map (comp annotate-keyword #(str ":" %)) keywords))

(defn keyword-candidates
  [ns]
  (let [keywords (all-keywords)]
    (concat
      (qualified-auto-resolved-keywords keywords ns)
      (unqualified-auto-resolved-keywords keywords ns)
      (keyword-namespace-aliases ns)
      (single-colon-keywords keywords))))

(defn namespaces
  [ns]
  (concat (map ns-name (all-ns)) (keys (ns-aliases ns))))

(defn ns-public-vars
  [ns]
  (vals (ns-publics ns)))

(defn ns-vars
  [ns]
  (filter var? (vals (ns-map ns))))

(defn ns-classes
  [ns]
  (keys (ns-imports ns)))

(defn- static?
  [^Member member]
  (-> member .getModifiers Modifier/isStatic))

(defn ns-java-methods
  [ns]
  (sequence
    (comp
      (map val)
      (mapcat #(.getMethods ^Class %))
      (filter static?)
      (map #(->> ^Member % .getName (str ".")))
      (distinct))
    (ns-imports ns)))

(defn static-members
  [^Class class]
  (sequence
    (comp
      (filter static?)
      (map #(.getName ^Member %))
      (dedupe))
    (concat (.getMethods class) (.getDeclaredFields class))))

(defn path-files [^String path]
  (cond
    (.endsWith path "/*")
    (for [^File jar (.listFiles (File. path)) :when (.endsWith ^String (.getName jar) ".jar")
          file (path-files (.getPath jar))]
      file)

    (.endsWith path ".jar")
    (try (for [^JarEntry entry (enumeration-seq (.entries (JarFile. path)))]
           (.getName entry))
      (catch Exception e))

    :else
    (for [^File file (file-seq (File. path))]
      (.replace ^String (.getPath file) path ""))))

(def classfiles
  (delay
    (for [prop (filter #(System/getProperty %1) ["sun.boot.class.path" "java.ext.dirs" "java.class.path"])
          path (.split (System/getProperty prop) File/pathSeparator)
          ^String file (path-files path) :when (and (.endsWith file ".class") (not (.contains file "__")))]
      file)))

(defn- classname [^String file]
  (.. file (replace ".class" "") (replace File/separator ".")))

(defn annotate-class
  [class-name]
  {:candidate (name class-name) :type :class})

(def system-module-resources
  (future
    (try
      (when-some [module-finder (Class/forName "java.lang.module.ModuleFinder")]
        (->>
          (Reflector/invokeStaticMethod module-finder "ofSystem" (into-array Object []))
          .findAll
          (sequence
            (comp
              (mapcat #(-> % .open .list .iterator iterator-seq))
              (map classname)
              (map annotate-class)))
          (sort-by :candidate)))
      (catch ClassNotFoundException _))))

(def top-level-classes
  (future
    (->>
      (sequence
        (comp
          (filter #(re-find #"^[^\$]+\.class" %))
          (map classname)
          (map annotate-class))
        @classfiles)
      (sort-by :candidate))))

(def nested-classes
  (future
    (->>
      (sequence
        (comp
          (filter #(re-find #"^[^\$]+(\$[^\d]\w*)+\.class" %))
          (map classname)
          (map annotate-class))
        @classfiles)
      (sort-by :candidate))))

(defn resolve-class [ns sym]
  (try (let [val (ns-resolve ns sym)]
         (when (class? val) val))
    (catch Exception e
      (when (not= ClassNotFoundException
              (class (main/repl-exception e)))
        (throw e)))))

(defn annotate-var [var]
  (let [{macro :macro arglists :arglists var-name :name doc :doc} (meta var)
        type (cond macro :macro arglists :function :else :var)]
    (cond-> {:candidate (name var-name) :type type}
      doc (assoc :doc doc)
      arglists (assoc :arglists (map pr-str arglists)))))

(def class-candidate-list
  (delay (concat @system-module-resources @top-level-classes @nested-classes)))

(def special-forms
  '[def if do let quote var fn loop recur throw try monitor-enter monitor-exit dot new set!])

(defn special-form-candidates
  []
  (map #(hash-map :candidate (name %) :type :special-form :ns "clojure.core") special-forms))

(defn annotate-namespace
  [ns]
  {:candidate (name ns) :type :namespace})

(defn ns-candidates
  [ns]
  (map #(let [doc (some-> % find-ns meta :doc)]
          (cond-> (annotate-namespace %)
            doc (assoc :doc doc)))
    (namespaces ns)))

(defn ns-var-candidates
  [ns]
  (map annotate-var (ns-vars ns)))

(defn ns-public-var-candidates
  [ns]
  (map annotate-var (ns-public-vars ns)))

(defn ns-class-candidates
  [ns]
  (map #(hash-map :candidate (name %) :type :class) (ns-classes ns)))

(defn ns-java-method-candidates
  [ns]
  (map #(hash-map :candidate % :type :method) (ns-java-methods ns)))

(defn static-member-candidates
  [class]
  (map #(hash-map :candidate % :type :static-method) (static-members class)))

(defn scoped-candidates
  [^String prefix ns]
  (when-let [prefix-scope (first (.split prefix "/"))]
    (let [scope (symbol prefix-scope)
          candidates (if-let [class (resolve-class ns scope)]
                       (static-member-candidates class)
                       (when-let [ns (or (find-ns scope) (scope (ns-aliases ns)))]
                         (ns-public-var-candidates ns)))]
      (map #(update % :candidate (fn [c] (str scope "/" c))) candidates))))

(defn candidate?
  [^String prefix {:keys [^String candidate]}]
  (.startsWith candidate prefix))

(defn class-candidates
  [^String prefix]
  (let [candidate? (partial candidate? prefix)]
    (sequence
      (comp
        (remove #(and (not (.contains prefix "$")) (.contains ^String (:candidate %) "$")))
        (drop-while (complement candidate?))
        (take-while candidate?))
      @class-candidate-list)))

(defn generic-candidates
  [ns]
  (concat
    (special-form-candidates)
    (ns-candidates ns)
    (ns-var-candidates ns)
    (ns-class-candidates ns)))

(defn candidates
  [^String prefix ns]
  (when (seq prefix)
    (let [candidates (cond
                       (.startsWith prefix ":") (keyword-candidates ns)
                       (.startsWith prefix ".") (ns-java-method-candidates ns)
                       (and (not (.startsWith prefix "/")) (.contains prefix "/")) (scoped-candidates prefix ns)
                       (.contains prefix ".") (concat (ns-candidates ns) (class-candidates prefix))
                       :else (generic-candidates ns))]
      (sort-by :candidate (filter #(candidate? prefix %) candidates)))))

(defmulti completions :dialect)

(defmethod completions :default
  [{:keys [prefix ns out-fn] :as message}]
  (let [ns (or (some-> ns symbol find-ns) (the-ns 'user))]
    (out-fn (response-for message {:completions (candidates prefix ns)}))))

(defmethod handle :completions
  [message]
  (completions message))

(comment
  (completions "main/" *ns*)
  (time (dorun (completions ":a" *ns*)))
  (time (dorun (completions "m" *ns*)))
  (time (dorun (completions "clojure." *ns*)))
  (time (dorun (completions "java." *ns*)))
  (time (dorun (completions "java.r" *ns*)))
  (time (dorun (completions "java.time.LocalDate/" *ns*)))
  )
