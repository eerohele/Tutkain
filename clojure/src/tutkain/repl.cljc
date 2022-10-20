(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint]
   [tutkain.backchannel :as backchannel]
   [tutkain.format :as format])
  (:import
   (java.io Writer)
   (java.util.concurrent Executors TimeUnit ThreadPoolExecutor$CallerRunsPolicy)))

(def ^:dynamic ^:experimental *print*
  "A function you can use as the :print arg of clojure.main/repl."
  prn)

(def ^:dynamic ^:experimental *caught*
  "A function you can use as the :caught arg of clojure.main/repl."
  #?(:bb pr-str :clj main/repl-caught))

(defn ^:private read-in-context
  "Given a tutkain.backchannel.Backchannel and a LineNumberingPushbackReader,
  read a form from the reader in the context of the eval context thread
  bindings and return the eval context with these keys added:

  - :form - The object read
  - :string - The string read"
  [backchannel ^clojure.lang.LineNumberingPushbackReader reader]
  (.unread reader (.read reader))
  ;; If there's no new eval context immediately available, use the previous set
  ;; of thread bindings.
  ;;
  ;; This way, if the user sends more than one form at once, we use the same
  ;; eval context for each form instead of waiting for a new one after every
  ;; form.
  (let [eval-context (backchannel/eval-context backchannel)
        [form string] (with-bindings (not-empty (:thread-bindings eval-context))
                        #?(:bb (read+string reader false ::EOF)
                           :clj (read+string {:eof ::EOF :read-cond :allow} reader)))]
    (assoc eval-context :form form :string string)))

(defn ^:private make-debouncer
  [service]
  (fn [f delay]
    (let [task (atom nil)]
      (fn [& args]
        (some-> @task (.cancel false))
        (reset! task
          (.schedule service
            (fn []
              (apply f args)
              (reset! task nil))
            delay
            TimeUnit/MILLISECONDS))))))

(defn ^:private default-init
  []
  (in-ns 'user)
  (apply require main/repl-requires))

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
  ([{:keys [init] :as opts}]
   (let [print-lock (Object.)
         eval-lock (Object.)
         out *out*
         in *in*
         pretty-print (fn [message]
                        (binding [*print-readably* true
                                  pprint/*print-right-margin* 100]
                          (locking print-lock
                            (pprint/pprint message out))))
         repl-thread (Thread/currentThread)
         debounce-service (doto (Executors/newScheduledThreadPool 1)
                            (.setRejectedExecutionHandler (ThreadPoolExecutor$CallerRunsPolicy.)))
         debounce (make-debouncer debounce-service)]
     (main/with-bindings
       ((requiring-resolve (or init `default-init)))
       (let [backchannel (backchannel/open
                           (assoc opts
                             :bindings (get-thread-bindings)
                             :xform-in #(assoc % :eval-lock eval-lock :in in :repl-thread repl-thread)
                             :xform-out #(dissoc % :in)))
             ;; Prevent stdout/stderr from interleaving with eval results by
             ;; binding *out* and *err* such that they write into auxiliary
             ;; PrintWriters that send strings to client via backchannel, then
             ;; debounce flush said auxiliary PrintWriters.
             out-writer (PrintWriter-on #(backchannel/send-to-client backchannel {:tag :out :val %1}) nil)
             err-writer (PrintWriter-on #(backchannel/send-to-client backchannel {:tag :err :val %1}) nil)
             flush-out (debounce #(.flush out-writer) 50)
             flush-err (debounce #(.flush err-writer) 50)
             write-out (fn [string] (.write out-writer string) (flush-out))
             write-err (fn [string] (.write err-writer string) (flush-err))]
         (binding [*out* (PrintWriter-on write-out #(.close out-writer))
                   *err* (PrintWriter-on write-err #(.close err-writer))
                   *print* pretty-print]
           (try
             (pretty-print {:greeting (str "Clojure " (clojure-version) "\n")
                            :host (backchannel/host backchannel)
                            :port (backchannel/port backchannel)})
             (loop []
               (when
                 (try
                   (let [{:keys [thread-bindings response form string]} (read-in-context backchannel in)
                         ;; For (read-line) support. See also:
                         ;;
                         ;; https://clojure.atlassian.net/browse/CLJ-2692
                         _ (skip-whitespace in)
                         backchannel-response? (#{:inline :clipboard} (:output response))]
                     (with-bindings thread-bindings
                       (when-not (identical? form ::EOF)
                         (try
                           (let [ret (locking eval-lock (eval form))]
                             (.flush ^Writer *out*)
                             (.flush ^Writer *err*)
                             (when-not (= :repl/quit ret)
                               (set! *3 *2)
                               (set! *2 *1)
                               (set! *1 ret)
                               (if backchannel-response?
                                 (backchannel/send-to-client backchannel
                                   (assoc response :tag :ret :val (format/pp-str ret)))
                                 (pretty-print ret))
                               (backchannel/update-thread-bindings backchannel (get-thread-bindings))
                               true))
                           (catch Throwable ex
                             (.flush ^Writer *out*)
                             (.flush ^Writer *err*)
                             (set! *e ex)
                             (backchannel/send-to-client backchannel
                               (merge response {:tag :err
                                                :val (format/Throwable->str ex)
                                                :ns (str *ns*)
                                                :form string}))
                             (backchannel/update-thread-bindings backchannel (get-thread-bindings))
                             true)))))
                   (catch Throwable ex
                     (set! *e ex)
                     (backchannel/send-to-client backchannel
                       {:tag :ret
                        :val (format/pp-str (assoc (Throwable->map ex) :phase :read-source))
                        :ns (str *ns*)
                        :exception true})
                     (backchannel/update-thread-bindings backchannel (get-thread-bindings))
                     true))
                 (recur)))
             (finally
               (.shutdown debounce-service)
               (backchannel/close backchannel)))))))))