(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [tutkain.pprint :as pprint]
   [tutkain.rpc :as rpc]
   [tutkain.format :as format])
  (:import
   (java.io Writer)))

(def ^:dynamic ^:experimental *print*
  "A function you can use as the :print arg of clojure.main/repl."
  prn)

(def ^:dynamic ^:experimental *caught*
  "A function you can use as the :caught arg of clojure.main/repl."
  #?(:bb pr-str :clj main/repl-caught))

(defn ^:private read-in-context
  "Given a tutkain.rpc.RPC and a LineNumberingPushbackReader,
  read a form from the reader in the context of the backchannel thread
  bindings and return a map with these keys:

  - :form - The object read
  - :thread-bindings - The backchannel thread bindings"
  [backchannel ^clojure.lang.LineNumberingPushbackReader reader]
  (.unread reader (.read reader))
  (let [thread-bindings (rpc/thread-bindings backchannel)
        [form _] (with-bindings (not-empty thread-bindings)
                   (try
                     #?(:bb (read+string reader false ::EOF)
                        :clj (read+string {:eof ::EOF :read-cond :allow} reader))
                     (catch Throwable ex
                       (throw (ex-info nil {:clojure.error/phase :read-source} ex)))))]
    ;; After picking up the thread bindings sent via the backchannel, clear
    ;; them to signal to the REPL that it is OK to update them after
    ;; evaluation.
    (rpc/clear-thread-bindings backchannel)
    {:thread-bindings thread-bindings :form form}))

;; Vendored in from clojure.main -- Babashka doesn't have this.
(defn ^:private skip-whitespace
  "Skips whitespace characters on stream s. Returns :line-start, :stream-end,
  or :body to indicate the relative location of the next character on s.
  Interprets comma as whitespace and semicolon as comment to end of line.
  Does not interpret #! as comment to end of line because only one
  character of lookahead is available. The stream must either be an
  instance of LineNumberingPushbackReader or duplicate its behavior of both
  supporting .unread and collapsing all of CR, LF, and CRLF to a single
  \\newline."
  [s]
  (loop [c (.read s)]
    (cond
     (= c (int \newline)) :line-start
     (= c -1) :stream-end
     (= c (int \;)) (do (.readLine s) :line-start)
     (or (Character/isWhitespace (char c)) (= c (int \,))) (recur (.read s))
     :else (do (.unread s c) :body))))

(defmacro ^:private with-repl
  "Execute body with clojure.core/*repl* bound to true iff clojure.core/*repl*
  is defined.

  For compatibility with clojure.repl.deps when using a new enough version of
  Clojure."
  [& body]
  `(if-some [v# (requiring-resolve 'clojure.core/*repl*)]
     (with-bindings {v# true}
       (do ~@body))
     (do ~@body)))

(defn repl
  "Tutkain's main read-eval-print loop.

  - Starts a backchannel socket server that Tutkain uses for editor tooling
    (auto-completion, metadata lookup, etc.)
  - Pretty-prints evaluation results and exception maps
  - Binds *print* for use with nested REPLs started via
    clojure.main/repl"
  ([]
   (repl {}))
  ([{:keys [init] :or {init `rpc/default-init} :as opts}]
   (try
     (let [print-lock (Object.)
           eval-lock (Object.)
           eval-future (atom nil)
           out *out*
           in *in*
           pretty-print (fn [message]
                          (binding [*print-readably* true]
                            (locking print-lock
                              (pprint/pprint out message {:map-entry-separator "" :max-width 100})
                              (.flush out))))
           repl-thread (Thread/currentThread)]
       (main/with-bindings
         (with-repl
           (rpc/resolve-and-apply init `rpc/default-init)
           (let [backchannel (rpc/open
                               (assoc opts
                                 :bindings (get-thread-bindings)
                                 :xform-in #(assoc % :eval-lock eval-lock :eval-future eval-future :in in :repl-thread repl-thread)
                                 :xform-out #(dissoc % :in)))]
             (binding [*out* (PrintWriter-on #(rpc/write-out backchannel %1) nil)
                       *err* (PrintWriter-on #(rpc/write-err backchannel %1) nil)
                       *print* pretty-print]
               (try
                 (pretty-print {:host (rpc/host backchannel) :port (rpc/port backchannel)})
                 (println "Clojure" (clojure-version) "(Java" (str (Runtime/version) ")"))
                 (loop []
                   (when
                     (try
                       (let [{:keys [thread-bindings form]} (read-in-context backchannel in)
                             ;; For (read-line) support. See also:
                             ;;
                             ;; https://clojure.atlassian.net/browse/CLJ-2692
                             _ (skip-whitespace in)]
                         (with-bindings thread-bindings
                           (when-not (identical? form ::EOF)
                             (try
                               (let [ret (locking eval-lock (eval form))]
                                 (.flush ^Writer *out*)
                                 (.flush ^Writer *err*)
                                 (when-not (#{{:op :quit} :repl/quit} ret)
                                   (set! *3 *2)
                                   (set! *2 *1)
                                   (set! *1 ret)
                                   (try
                                     (pretty-print ret)
                                     (catch Throwable ex
                                       (rpc/write-err backchannel
                                         (format/Throwable->str (ex-info nil {:clojure.error/phase :print-eval-result} ex)))))
                                   (rpc/update-thread-bindings backchannel (get-thread-bindings))
                                   true))
                               (catch InterruptedException _
                                 (rpc/write-err backchannel ":interrupted\n"))
                               (catch Throwable ex
                                 (.flush ^Writer *out*)
                                 (.flush ^Writer *err*)
                                 (set! *e ex)
                                 (rpc/write-err backchannel (format/Throwable->str ex))
                                 (rpc/update-thread-bindings backchannel (get-thread-bindings))
                                 true)))))
                       (catch Throwable ex
                         (set! *e ex)
                         (rpc/write-err backchannel (format/Throwable->str ex))
                         (rpc/update-thread-bindings backchannel (get-thread-bindings))
                         true))
                     (recur)))
                 (finally
                   (rpc/close backchannel))))))))
     (catch Exception ex
       {:tag :err :val (with-out-str (pprint/pprint (Throwable->map ex)))}))))
