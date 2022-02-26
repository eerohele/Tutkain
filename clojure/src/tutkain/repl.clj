(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint]
   [clojure.repl :as repl]
   [tutkain.backchannel :as backchannel]
   [tutkain.format :as format]))

(def ^:dynamic ^:experimental *print*
  "A function you can use as the :print arg of clojure.main/repl."
  prn)

(def ^:dynamic ^:experimental *caught*
  "A function you can use as the :caught arg of clojure.main/repl."
  main/repl-caught)

(defmacro switch-ns
  [namespace]
  `(or (some->> '~namespace find-ns ns-name in-ns .name) (ns ~namespace)))

(defn pst
  "Like clojure.repl/pst, but doesn't print in a doseq so as to be faster and
  to avoid interleaving.

  Adapted from clojure.repl/pst:

  https://github.com/clojure/clojure/blob/5451cee06b9e31513a19e596e4e155d1f08d2a8d/src/clj/clojure/repl.clj#L240-L268"
  ([] (pst 12))
  ([e-or-depth]
   (if (instance? Throwable e-or-depth)
     (pst e-or-depth 12)
     (when-let [e *e]
       (pst (repl/root-cause e) e-or-depth))))
  ([^Throwable e depth]
   (let [sb (StringBuffer.)]
     (binding [*out* *err*]
       (when (#{:read-source :macro-syntax-check :macroexpansion :compile-syntax-check :compilation}
              (-> e ex-data :clojure.error/phase))
         (.append sb "Note: The following stack trace applies to the reader or compiler, your code was not executed.\n"))
       (.append sb (str (-> e class .getSimpleName) " "
                     (.getMessage e)
                     (when-let [info (ex-data e)] (str " " (pr-str info)))
                     \newline))
       (let [st (.getStackTrace e)
             cause (.getCause e)]
         (doseq [el (take depth
                      (remove #(#{"clojure.lang.RestFn" "clojure.lang.AFn"} (.getClassName %))
                        st))]
           (.append sb (str \tab (repl/stack-element-str el) \newline)))
         (print (str sb))
         (flush)
         (when cause
           (println "Caused by:")
           (pst cause (min depth
                        (+ 2 (- (count (.getStackTrace cause))
                               (count st)))))))))))

(defn ^:private read-in-context
  "Given an eval context and a LineNumberingPushbackReader, read a form from
  the reader in the context of the eval context thread bindings and return
  the eval context with these keys added:

  - :form - The object read
  - :string - The string read"
  [eval-context ^clojure.lang.LineNumberingPushbackReader reader]
  (.unread reader (.read reader))
  (let [eval-context @eval-context
        [form string] (with-bindings (:thread-bindings eval-context {})
                        (read+string {:eof ::EOF :read-cond :allow} reader))]
    (assoc eval-context :form form :string string)))

(defn repl
  "Tutkain's main read-eval-print loop.

  - Starts a backchannel socket server that Tutkain uses for editor tooling
    (auto-completion, metadata lookup, etc.)
  - Pretty-prints evaluation results and exception maps
  - Binds *print* for use with nested REPLs started via
    clojure.main/repl"
  ([]
   (repl {}))
  ([opts]
   (let [lock (Object.)
         out *out*
         in *in*
         pretty-print (fn [message]
                        (binding [*print-readably* true
                                  pprint/*print-right-margin* 100]
                          (locking lock
                            (pprint/pprint message out))))
         repl-thread (Thread/currentThread)]
     (main/with-bindings
       (in-ns 'user)
       (apply require main/repl-requires)
       (let [{backchannel :socket
              eval-context :eval-context
              send-over-backchannel :send-over-backchannel}
             (backchannel/open
               (assoc opts
                 :xform-in #(assoc % :in in :repl-thread repl-thread)
                 :xform-out #(dissoc % :in)))]
         (binding [*out* (PrintWriter-on #(send-over-backchannel {:tag :out :val %1}) nil)
                   *err* (PrintWriter-on #(send-over-backchannel {:tag :err :val %1}) nil)
                   *print* pretty-print]
           (try
             (pretty-print {:greeting (str "Clojure " (clojure-version) "\n")
                            :host (-> backchannel .getInetAddress .getHostName)
                            :port (-> backchannel .getLocalPort)})
             (loop []
               (when
                 (try
                   (let [{:keys [thread-bindings response form string]} (read-in-context eval-context in)
                         ;; For (read-line) support. See also:
                         ;;
                         ;; https://clojure.atlassian.net/browse/CLJ-2692
                         _ (main/skip-whitespace in)
                         backchannel-response? (#{:inline :clipboard} (:output response))]
                     (with-bindings thread-bindings
                       (when-not (identical? form ::EOF)
                         (try
                           (let [ret (eval form)]
                             (when-not (= :repl/quit ret)
                               (set! *3 *2)
                               (set! *2 *1)
                               (set! *1 ret)
                               (if backchannel-response?
                                 (send-over-backchannel
                                   (assoc response :tag :ret :val (format/pp-str ret)))
                                 (pretty-print ret))
                               (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                               (flush)
                               true))
                           (catch Throwable ex
                             (set! *e ex)
                             (send-over-backchannel
                               (merge response {:tag :err
                                                :val (format/Throwable->str ex)
                                                :ns (str (.name *ns*))
                                                :form string}))
                             (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                             (flush)
                             true)))))
                   (catch Throwable ex
                     (set! *e ex)
                     (send-over-backchannel
                       {:tag :ret
                        :val (format/pp-str (assoc (Throwable->map ex) :phase :read-source))
                        :ns (str (.name *ns*))
                        :exception true})
                     (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                     true))
                 (recur)))
             (finally
               (.close backchannel)))))))))
