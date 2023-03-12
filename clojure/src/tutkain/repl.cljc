(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint]
   [tutkain.backchannel :as backchannel]
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
  "Given a tutkain.backchannel.Backchannel and a LineNumberingPushbackReader,
  read a form from the reader in the context of the backchannel thread
  bindings and return a map with these keys:

  - :form - The object read
  - :thread-bindings - The backchannel thread bindings"
  [backchannel ^clojure.lang.LineNumberingPushbackReader reader]
  (.unread reader (.read reader))
  (let [thread-bindings (backchannel/thread-bindings backchannel)
        [form _] (with-bindings (not-empty thread-bindings)
                        #?(:bb (read+string reader false ::EOF)
                           :clj (read+string {:eof ::EOF :read-cond :allow} reader)))]
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

(defn repl
  "Tutkain's main read-eval-print loop.

  - Starts a backchannel socket server that Tutkain uses for editor tooling
    (auto-completion, metadata lookup, etc.)
  - Pretty-prints evaluation results and exception maps
  - Binds *print* for use with nested REPLs started via
    clojure.main/repl"
  ([]
   (repl {}))
  ([{:keys [init] :or {init `backchannel/default-init} :as opts}]
   (let [print-lock (Object.)
         eval-lock (Object.)
         eval-future (atom nil)
         out *out*
         in *in*
         pretty-print (fn [message]
                        (binding [*print-readably* true
                                  pprint/*print-right-margin* 100]
                          (locking print-lock
                            (pprint/pprint message out))))
         repl-thread (Thread/currentThread)]
     (main/with-bindings
       (when-some [initf (or
                           (try (requiring-resolve init) (catch java.io.FileNotFoundException _))
                           (requiring-resolve `default-init))]
         (initf))
       (let [backchannel (backchannel/open
                           (assoc opts
                             :bindings (get-thread-bindings)
                             :xform-in #(assoc % :eval-lock eval-lock :eval-future eval-future :in in :repl-thread repl-thread)
                             :xform-out #(dissoc % :in)))]
         (binding [*out* (PrintWriter-on #(backchannel/write-out backchannel %1) nil)
                   *err* (PrintWriter-on #(backchannel/write-err backchannel %1) nil)
                   *print* pretty-print]
           (try
             (pretty-print {:host (backchannel/host backchannel) :port (backchannel/port backchannel)})
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
                               (pretty-print ret)
                               (backchannel/update-thread-bindings backchannel (get-thread-bindings))
                               true))
                           (catch Throwable ex
                             (.flush ^Writer *out*)
                             (.flush ^Writer *err*)
                             (set! *e ex)
                             (backchannel/write-err backchannel (format/Throwable->str ex))
                             (backchannel/update-thread-bindings backchannel (get-thread-bindings))
                             true)))))
                   (catch Throwable ex
                     (set! *e ex)
                     (backchannel/write-err backchannel (format/Throwable->str ex))
                     (backchannel/update-thread-bindings backchannel (get-thread-bindings))
                     true))
                 (recur)))
             (finally
               (backchannel/close backchannel)))))))))
