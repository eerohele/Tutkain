(ns tutkain.completions
  "Query the Clojure runtime for information on vars, keywords, Java classes,
  etc., presumably for editor auto-completion support.

  Originally adapted from nrepl.util.completion."
  (:require
   [clojure.string :as string]
   [clojure.zip :as zip]
   [tutkain.base64 :refer [base64-reader]]
   [tutkain.rpc :as rpc :refer [handle respond-to]]
   [tutkain.java :as java])
  (:import
   (java.io File Reader)
   (java.lang.reflect Field Member Method Modifier)
   (java.util.jar JarEntry JarFile)))

(when (nil? (System/getProperty "apple.awt.UIElement"))
  (System/setProperty "apple.awt.UIElement" "true"))

(defn annotate-keyword
  [kw]
  {:trigger kw :type :keyword})

(defn annotate-navigation
  [candidate]
  {:trigger (name candidate) :type :navigation})

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
  (eduction
    (map (fn [[ns-alias ns]]
           (eduction
             (filter #(= (namespace %) (str ns)))
             (map #(str "::" ns-alias "/" (name %)))
             (map annotate-keyword)
             keywords)))
    cat
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
  (eduction (map ns-name) (all-ns)))

(comment (namespaces) ,,,)

(defn namespace-aliases
  [ns]
  (keys (ns-aliases ns)))

(comment (namespace-aliases 'clojure.main) ,,,)

(defn- static?
  "Given a member of a class, return true if it is a static member."
  [^Member member]
  (-> member .getModifiers Modifier/isStatic))

(defn ns-instance-method-candidates
  "Given an ns symbol, return all Java instance methods that are available in
  the context of that ns."
  [ns]
  (eduction
    (map val)
    (mapcat #(.getMethods ^Class %))
    (map (fn [^Method method]
           {:class (-> method .getDeclaringClass java/qualified-class-name)
            :trigger (str "." (.getName method))
            :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes method))
            :return-type (-> method .getReturnType java/qualified-class-name)
            :type :instance-method}))
    (distinct)
    (ns-imports ns)))

(comment (seq (ns-instance-method-candidates 'clojure.main)))

(defn field-candidates
  "Given a java.lang.Class instance, return all field candidates of that class."
  [^Class class]
  (eduction
    (filter static?)
    (map #(hash-map :trigger (.getName ^Field %) :type :field))
    (.getDeclaredFields class)))

(comment (field-candidates java.lang.String) ,)

(defn ^:private method-candidates
  "Given a java.lang.Class instance, return all method candidates of that
  class."
  [xform ^Class class]
  (eduction
    (map (fn [^Method method]
           {:class (java/qualified-class-name class)
            :trigger (.getName method)
            :type (if (static? method) :static-method :instance-method)
            :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes method))
            :return-type (-> method .getReturnType java/qualified-class-name)}))
    xform
    (.getMethods class)))

(defn constructor-candidates
  [class]
  (eduction
    (map (fn [^java.lang.reflect.Constructor constructor]
           (let [class-name (java/qualified-class-name class)]
             {:class class-name
              :trigger "new"
              :type :constructor
              :arglists (mapv (memfn ^Class getSimpleName) (.getParameterTypes constructor))
              :return-type class-name})))
    (.getConstructors class)))

(comment (seq (constructor-candidates java.lang.String)) ,,,)

(defn static-method-candidates
  [class]
  (method-candidates (filter (comp #{:static-method} :type)) class))

(comment (seq (static-method-candidates java.lang.String)),)

(defn annotate-class
  [class-name]
  {:trigger (name class-name) :type :class})

(defn annotate-var [var]
  (let [{macro :macro arglists :arglists var-name :name doc :doc} (meta var)
        type (cond macro :macro arglists :function :else :var)]
    (cond-> {:trigger (name var-name) :type type}
      doc (assoc :doc doc)
      arglists (assoc :arglists (map pr-str arglists)))))

(defn path-files
  [^String path]
  (cond
    (.endsWith path "/*")
    (eduction
      (filter #(.endsWith ^String (.getName ^File %) ".jar"))
      (mapcat #(-> ^File % .getPath path-files))
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
            ;; Remove classes such as clojure.core$_ and
            ;; clojure.core$bounded_count no-one ever wants to
            ;; import.
            (remove #(re-find #".+\$\P{Lu}.*" %))
            (map #(.. ^String % (replace ".class" "") (replace "/" ".")))
            (map annotate-class)
            (.split (System/getProperty "java.class.path") File/pathSeparator))))

(defn ^:private base-classes
  "Return a sequence of all java.* and javax.* classes in every Java module in
  the current JDK."
  []
  #?(:bb (map (fn [class] (annotate-class (.getName class))) (babashka.classes/all-classes))
     :clj (let [module-finder (java.lang.module.ModuleFinder/ofSystem)]
            (eduction
              cat
              ;; Remove anonymous nested classes
              (remove #(re-find #".+\$\d.+\.class" %))
              (map #(.. ^String % (replace ".class" "") (replace "/" ".")))
              ;; Only retain java.* and javax.* to limit memory consumption
              (filter #(or (.startsWith ^String % "java.") (.startsWith ^String % "javax.") (.startsWith ^String % "jdk.")))
              (remove #(re-find #".+\$\d.*" %))
              (map annotate-class)
              (for [^java.lang.module.ModuleReference module-reference (.findAll module-finder)]
                (with-open [module-reader (.open module-reference)
                            stream (.list module-reader)]
                  (iterator-seq (.iterator stream))))))))

(def ^:private all-class-candidates
  (future
    (into (sorted-set-by (fn [x y] (compare (:trigger x) (:trigger y))))
      (concat (non-base-classes) (base-classes)))))

(defn ^:private nested-class-names
  []
  (filter #(.contains ^String (:trigger %) "$")
    @all-class-candidates))

(def special-form-candidates
  "All Clojure special form candidates."
  [{:trigger "def" :ns "clojure.core" :type :special-form}
   {:trigger "do" :ns "clojure.core" :type :special-form}
   {:trigger "dot" :ns "clojure.core" :type :special-form}
   {:trigger "fn" :ns "clojure.core" :type :special-form}
   {:trigger "if" :ns "clojure.core" :type :special-form}
   {:trigger "let" :ns "clojure.core" :type :special-form}
   {:trigger "loop" :ns "clojure.core" :type :special-form}
   {:trigger "monitor-enter" :ns "clojure.core" :type :special-form}
   {:trigger "monitor-exit" :ns "clojure.core" :type :special-form}
   {:trigger "new" :ns "clojure.core" :type :special-form}
   {:trigger "quote" :ns "clojure.core" :type :special-form}
   {:trigger "recur" :ns "clojure.core" :type :special-form}
   {:trigger "set!" :ns "clojure.core" :type :special-form}
   {:trigger "throw" :ns "clojure.core" :type :special-form}
   {:trigger "try" :ns "clojure.core" :type :special-form}
   {:trigger "var" :ns "clojure.core" :type :special-form}])

(defn annotate-namespace
  [ns]
  {:trigger (name ns) :type :namespace})

(defn ns-candidates
  "Return all namespace candidates"
  []
  (map (fn [ns]
         (let [doc (some-> ns find-ns meta :doc)]
           (cond-> (annotate-namespace (name ns)) doc (assoc :doc doc))))
    (sort (namespaces))))

(comment (ns-candidates) ,,,)

(defn ns-alias-candidates
  "Given an ns symbol, return all namespace aliases in the ns."
  [ns]
  (map annotate-navigation (namespace-aliases ns)))

(comment (ns-alias-candidates 'clojure.main),)

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

(defn instance-method-candidates
  "Given a java.lang.Class instance, return all instance method candidates of that
  class."
  [^Class class]
  (method-candidates
    (comp
      (filter (comp #{:instance-method} :type))
      (map #(update % :trigger (fn [trigger] (str "." trigger)))))
    class))

(comment (seq (instance-method-candidates java.io.File)) ,,,)

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
                       (concat
                         (constructor-candidates class)
                         (static-method-candidates class)
                         (field-candidates class)
                         (instance-method-candidates class))
                       (concat
                         (some-> scope find-ns ns-public-var-candidates)
                         (some-> ns ns-aliases scope ns-public-var-candidates)))]
      (map (fn [candidate] (update candidate :trigger #(str scope "/" %))) candidates))))

(defn candidate?
  "Given a string prefix and a candidate map, return true if the trigger
  starts with the prefix."
  [^String prefix {:keys [^String trigger]}]
  (.startsWith trigger prefix))

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
  (sort-by :trigger (filter #(candidate? prefix %) candidates)))

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
      (candidates-for-prefix prefix (ns-instance-method-candidates ns))

      (scoped? prefix)
      (candidates-for-prefix prefix (scoped-candidates prefix ns))

      (and (.contains prefix ".") (.contains prefix "$"))
      (nested-class-candidates prefix)

      (.contains prefix ".")
      (concat
        (candidates-for-prefix prefix (ns-candidates))
        (candidates-for-prefix prefix (ns-alias-candidates ns))
        (class-candidates prefix))

      :else
      (candidates-for-prefix prefix
        (concat special-form-candidates
          (ns-candidates)
          (ns-alias-candidates ns)
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

(defn annotate-local
  [local]
  {:trigger (name local) :type :local})

(defmacro ^:private maybe-require-fn
  "Given a symbol naming a function, resolve and return that function.

  If the function is not found, return a function that always returns nil."
  [sym]
  `(or
     (some->
       (try
         (requiring-resolve '~sym)
         (catch Exception ex#))
       deref)
     (constantly nil)))

(def ^:private local-symbols
  (maybe-require-fn tutkain.analyzer.jvm/local-symbols))

(def ^:private read-forms
  (maybe-require-fn tutkain.analyzer/read-forms))

(defn local-completions
  [forms {:keys [prefix] :as message}]
  (try
    (let [locals (local-symbols (assoc message :forms forms))]
      (vec
        (candidates-for-prefix prefix
          (map annotate-local locals))))
    ;; If we're in a context tools.analyzer can't analyze (for example, (-> )),
    ;; give up on trying to figure out local completions. This way, we'll
    ;; still at least get global completions.
    (catch Exception _ [])))

(defn find-loc
  [form target-line target-column]
  (let [root (zip/seq-zip form)]
    (loop [loc root max-loc nil]
      (let [node (zip/node loc)
            {:keys [line column end-column]
             :or {line -1 column -1 end-column -1}} (meta node)]
        (cond
          (zip/end? loc)
          max-loc

          (and (= line target-line) (<= column target-column end-column))
          (recur (zip/next loc) loc)

          :else
          (recur (zip/next loc) max-loc))))))

(defn require-completions
  [loc prefix]
  ;; When e.g. [clojure.set :refer []], suggest vars in clojure.set.
  (let [node (some-> loc zip/node)]
    (cond
      (and (sequential? node) (= :refer (second node)))
      (candidates-for-prefix prefix (ns-public-var-candidates (first node)))

      ;; require without braces (e.g. (require 'foo.bar))
      (= '(require) node)
      (candidates-for-prefix prefix (ns-candidates))

      :else
      (map (fn [{:keys [trigger] :as candidate}]
             (case trigger
               "clojure.test"
               (assoc candidate
                 :completion "clojure.test ${5::refer [${1:deftest} ${2:is} ${3:use-fixtures}$4]}$0"
                 :completion-format :snippet)

               "clojure.tools.logging"
               (assoc candidate
                 :completion "clojure.tools.logging :as ${1:log}$0"
                 :completion-format :snippet)

               (let [parts (string/split trigger #"\.")
                     snippet (format "${1:%s}" (last parts))
                     completion (str trigger " ${2::as " snippet "}$0")]
                 (assoc candidate :completion completion :completion-format :snippet))))
        (candidates-for-prefix prefix (ns-candidates))))))

(defn import-completions
  [loc prefix]
  (let [head (some-> loc zip/node first)]
    (cond
      ;; import without parens (e.g. (import 'foo.bar.Baz))
      (= 'import head)
      (class-candidates prefix)

      (symbol? head)
      (map (fn [candidate]
             (update candidate :trigger (fn [trigger] (-> trigger (string/split #"\.") (last)))))
        (class-candidates (str (name head) "." prefix)))

      :else
      (map
        (fn [{:keys [trigger] :as candidate}]
          (let [parts (string/split trigger #"\.")
                ;; Escape $ to avoid snippet interference
                snippet (format "${1:%s}" (string/replace (last parts) "$" "\\$"))
                package (string/join \. (butlast parts))
                completion (str package " " snippet)]
            (assoc candidate :completion completion :completion-format :snippet)))
        (class-candidates prefix)))))

(def ns-form-snippets
  [{:type :keyword
    :trigger ":require"
    :completion-format :snippet
    :completion ":require [$0]"}
   {:type :keyword
    :trigger ":import"
    :completion-format :snippet
    :completion ":import ($0)"}
   {:type :keyword
    :trigger ":refer-clojure"
    :completion-format :snippet
    :completion ":refer-clojure :exclude [$0]"}])

(defn ns-form-completions
  [form prefix line column]
  (let [loc (find-loc form line column)
        node (some-> loc zip/node)
        head (some-> loc zip/leftmost zip/node)]
    (case head
      :require (require-completions loc prefix)
      :import (import-completions loc prefix)
      :refer-clojure (ns-public-var-candidates 'clojure.core)
      (case (first node)
        :require (candidates-for-prefix prefix (ns-candidates))
        :import (class-candidates prefix)
        ns-form-snippets))))

(defn context-completions
  [form prefix line column]
  (if-some [head (first form)]
    (if (symbol? head)
      (let [sym (some-> head resolve symbol)]
        (case sym
          clojure.core/ns (ns-form-completions form prefix line column)
          clojure.core/require (let [loc (find-loc form line column)]
                                 (require-completions loc prefix))
          clojure.core/import (let [loc (find-loc form line column)]
                                (import-completions loc prefix))
          ::none))
      ::none)
    ::none))

(defn ^:private find-completions
  [{:keys [file ns prefix enclosing-sexp start-line start-column line column] :as message}]
  (let [forms (when (seq enclosing-sexp)
                (with-open [^Reader reader (binding [*file* file *ns* ns]
                                             (base64-reader enclosing-sexp))]
                  (try
                    (read-forms
                      reader
                      {:features #{:clj :t.a.jvm} :read-cond :allow}
                      start-line
                      start-column)
                    (catch clojure.lang.ExceptionInfo _
                      []))))
        context-completions (context-completions (peek forms) prefix line column)]
    (if (identical? ::none context-completions)
      (into (local-completions forms message) (candidates prefix ns))
      context-completions)))

(defmethod completions :default
  [message]
  (try
    (let [completions (find-completions (assoc message :ns (rpc/namespace message)))]
      (respond-to message {:completions completions}))
    (catch Exception ex
      (respond-to message {:tag :err :debug true :val (pr-str (Throwable->map ex))}))))

(defmethod handle :completions
  [message]
  (completions message))
