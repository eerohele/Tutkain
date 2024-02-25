(ns tutkain.rpc
  (:refer-clojure :exclude [namespace])
  (:require
   [clojure.core :as core]
   [clojure.core.server :as server]
   [clojure.java.io :as io]
   [clojure.main :as main]
   [clojure.edn :as edn]
   [tutkain.base64 :as base64]
   [tutkain.format :as format]
   [tutkain.pprint :as pprint])
  (:import
   (clojure.lang LineNumberingPushbackReader RT)
   (java.nio.file LinkOption Files Paths Path)
   (java.io FileNotFoundException IOException StringReader Writer)
   (java.net ServerSocket SocketException URL)
   (java.util.concurrent Executors ExecutorService FutureTask ScheduledExecutorService TimeUnit ThreadFactory ThreadPoolExecutor ThreadPoolExecutor$CallerRunsPolicy)
   (java.util.concurrent.atomic AtomicInteger)))

(comment (set! *warn-on-reflection* true) ,,,)

(defn respond-to
  "Respond to a RPC op message."
  [{:keys [id out-fn]} response]
  (out-fn (cond-> response id (assoc :id id))))

(defmulti handle
  "Handle a RPC op message.

  Dispatches on :op."
  :op)

(defmethod handle :echo
  [message]
  (respond-to message {:op :echo}))

(defmethod handle :load-base64
  [{:keys [blob path filename requires] :as message}]
  (try
    (some->> requires (run! require))
    (try
      (base64/read-base64 blob path filename)
      (respond-to message {:tag :ret :val filename})
      (catch #?(:bb clojure.lang.ExceptionInfo :clj clojure.lang.Compiler$CompilerException) ex
        (respond-to message {:tag :err :val (format/Throwable->str ex)})))
    (catch FileNotFoundException ex
      (respond-to message {:tag :err :val (format/Throwable->str ex)}))))

(defmethod handle :default
  [message]
  (throw (ex-info "Unknown op" {:message message})))

(defn namespace
  "Given an RPC op message, return the clojure.lang.Namespace object the message
  implies."
  [{:keys [thread-bindings ns]}]
  (or (some-> ns symbol find-ns) (some-> thread-bindings deref (get #'*ns*)) (the-ns 'user)))

(defn set-line!
  [^LineNumberingPushbackReader reader line]
  (.setLineNumber reader (int line)))

;; Borrowed from https://github.com/nrepl/nrepl/blob/8223894f6c46a2afd71398517d9b8fe91cdf715d/src/clojure/nrepl/middleware/interruptible_eval.clj#L32-L40
(defn set-column!
  [^LineNumberingPushbackReader reader column]
  #?(:bb nil
     :clj (when-let [^java.lang.reflect.Field field (.getDeclaredField LineNumberingPushbackReader "_columnNumber")]
            (-> field (doto (.setAccessible true)) (.set reader (int column))))))

(defn ^:private find-or-create-ns
  "Given a namespace symbol, if the namespace named by the symbol already
  exists, return it.

  Otherwise, create a new namespace named by the symbol and refer all public
  vars clojure.core into it."
  [ns-sym]
  (when ns-sym
    (or (find-ns ns-sym)
      (let [new-ns (create-ns ns-sym)]
        (binding [*ns* new-ns] (refer-clojure))
        new-ns))))

(def ^:private classpath-root-paths
  (delay
    (sequence
      (comp
        (remove #(.contains ^String (.getPath ^URL %) ".jar!"))
        (map #(Paths/get (.toURI ^URL %))))
      (-> (RT/baseLoader) (.getResources "") (enumeration-seq)))))

(defn relative-to-classpath-root
  "Given a string path to a file, return the relative (to a classpath root) path
  to the file.

  If the file doesn't exist, return \"NO_SOURCE_PATH\"."
  [path-str]
  #?(:bb path-str
     :clj
     (if-some [^Path path (some-> path-str not-empty (Paths/get (into-array String [])))]
       (let [^String path-str (if (Files/exists path (into-array LinkOption []))
                                (let [^Path path (.toRealPath path (into-array LinkOption []))]
                                  (if-some [^Path root (some #(when (.startsWith path ^Path %) %) @classpath-root-paths)]
                                    (str (.relativize root path))
                                    path-str))
                                path-str)]
         (.replace path-str "\\" "/"))
       "NO_SOURCE_PATH")))

(defn ^:private make-thread-bindings
  [file ns]
  (let [bindings (cond-> {#'*file* (relative-to-classpath-root file)} ns (assoc #'*ns* ns))]
    #?(:bb bindings
       :clj (assoc bindings #'*source-path* (or (some-> file io/file .getName) "NO_SOURCE_FILE")))))

(defmethod handle :set-thread-bindings
  [{:keys [thread-bindings ^LineNumberingPushbackReader in ns file line column]
    :or {line 0 column 0} :as message}]
  (set-line! in line)
  (set-column! in column)
  (swap! thread-bindings merge (make-thread-bindings file (find-or-create-ns ns)))
  (respond-to message {:result :ok}))

(defn ^:private make-thread-factory
  [& {:keys [name-suffix]}]
  (reify ThreadFactory
    (newThread [_ runnable]
      (doto (Thread. runnable (format "tutkain.rpc/%s" (name name-suffix)))
        (.setDaemon true)))))

(defmethod handle :interrupt
  [{:keys [eval-future ^Thread repl-thread] :as message}]
  (try
    (when-some [^FutureTask f (some-> eval-future deref)]
      (.cancel f true))

    (some-> repl-thread .interrupt)
    (catch InterruptedException _
      (respond-to message {:tag :err :val ":interrupted\n"}))))

(defmulti evaluate :dialect)

(defn -update-thread-bindings
  [thread-bindings new-bindings]
  (swap! thread-bindings (fn [bindings] (if (nil? bindings) new-bindings bindings))))

(defmethod evaluate :default
  [{:keys [^ExecutorService eval-service eval-future eval-lock thread-bindings ns file line column code]
    :or {line 1 column 1}
    :as message}]
  (reset! eval-future
    (let [^Callable f (bound-fn []
                        (with-bindings (merge
                                         {#'*ns* (the-ns 'user) #'*e nil #'*1 nil #'*2 nil #'*3 nil}
                                         @thread-bindings
                                         (make-thread-bindings file (find-or-create-ns ns)))
                          (try
                            (with-open [reader (-> code StringReader. LineNumberingPushbackReader.)]
                              (set-line! reader line)
                              (set-column! reader column)
                              (run!
                                (fn [form]
                                  (try
                                    (let [ret (locking eval-lock (eval form))
                                          ;; If ret is a lazy seq, force it to force prints
                                          ;; from within the lazy seq (#124).
                                          ret (cond-> ret (seq? ret) doall)]
                                      (.flush ^Writer *out*)
                                      (.flush ^Writer *err*)
                                      (set! *3 *2)
                                      (set! *2 *1)
                                      (set! *1 ret)
                                      (reset! thread-bindings (get-thread-bindings))
                                      (respond-to message
                                        {:tag :ret
                                         :val (try
                                                (format/pp-str ret)
                                                (catch Throwable ex
                                                  (format/Throwable->str (ex-info nil {:clojure.error/phase :print-eval-result} ex))))}))
                                    (catch InterruptedException _
                                      (respond-to message {:tag :err :val ":interrupted\n"}))
                                    (catch Throwable ex
                                      (.flush ^Writer *out*)
                                      (.flush ^Writer *err*)
                                      (set! *e ex)
                                      (reset! thread-bindings (get-thread-bindings))
                                      (respond-to message {:tag :err :val (format/Throwable->str ex)}))))
                                (take-while #(not= % ::EOF)
                                  (repeatedly #(try
                                                 (read {:read-cond :allow :eof ::EOF} reader)
                                                 (catch Throwable ex
                                                   (throw (ex-info nil {:clojure.error/phase :read-source} ex))))))))
                            (catch Throwable ex
                              (set! *e ex)
                              (reset! thread-bindings (get-thread-bindings))
                              (respond-to message (merge (ex-data ex) {:tag :err :val (format/Throwable->str ex)}))))))]
      (.submit eval-service ^Callable f))))

(defmethod handle :eval
  [message]
  (evaluate message))

(defonce ^:private ^AtomicInteger thread-counter
  (AtomicInteger.))

(defn ^:private make-debouncer
  [^ScheduledExecutorService service]
  (fn [f ^long delay]
    (let [task (atom nil)]
      (fn [& args]
        (some-> ^FutureTask @task (.cancel false))
        (reset! task
          (.schedule service
            ^Callable
            (fn []
              (apply f args)
              (reset! task nil))
            delay
            TimeUnit/MILLISECONDS))))))

(defn accept
  [{:keys [add-tap? eventual-out-writer eventual-err-writer thread-bindings xform-in xform-out]
    :or {add-tap? false xform-in identity xform-out identity}}]
  (let [out *out*
        lock (Object.)
        out-fn (fn [message]
                 (binding [*print-length* nil
                           *print-level* nil
                           *print-meta* false
                           *print-namespace-maps* false
                           *print-readably* true]
                   (locking lock
                     (.write out (pr-str (dissoc (xform-out message) :out-fn :thread-bindings)))
                     (.write out "\n")
                     (.flush out))))
        tapfn #(out-fn {:tag :tap :val (format/pp-str %1)})
        ^ExecutorService debounce-service (doto ^ThreadPoolExecutor (Executors/newScheduledThreadPool 1 (make-thread-factory :name-suffix :debounce))
                                            (.setRejectedExecutionHandler (ThreadPoolExecutor$CallerRunsPolicy.)))
        ;;  ; ClojureScript does not use this. Add option to disable?
        eval-service (Executors/newSingleThreadExecutor (make-thread-factory :name-suffix :eval))
        eval-future (atom nil)
        debounce (make-debouncer debounce-service)]
    (when add-tap? (add-tap tapfn))
    (let [out-writer (PrintWriter-on #(out-fn {:tag :out :val %1}) nil)
          err-writer (PrintWriter-on #(out-fn {:tag :err :val %1}) nil)
          flush-out (debounce #(.flush out-writer) 50)
          flush-err (debounce #(.flush err-writer) 50)
          write-out (fn [^String string] (.write out-writer string) (flush-out))
          write-err (fn [^String string] (.write err-writer string) (flush-err))]
      (deliver eventual-out-writer write-out)
      (deliver eventual-err-writer write-err)
      (with-bindings @thread-bindings
        (try
          (binding [*out* (PrintWriter-on write-out #(.close out-writer))
                    *err* (PrintWriter-on write-err #(.close err-writer))]
            (loop []
              (let [recur?
                    (try
                      (let [message (edn/read {:eof ::EOF} *in*)]
                        (if (or (identical? ::EOF message) (= :quit (:op message)))
                          false
                          (let [message (assoc (xform-in message)
                                          :eval-service eval-service
                                          :eval-future eval-future
                                          :thread-bindings thread-bindings
                                          :out-fn out-fn)]
                            (try
                              (handle message)
                              (.flush ^Writer *err*)
                              true
                              (catch Throwable ex
                                (respond-to message {:tag :ret
                                                     :exception true
                                                     :val (format/pp-str (Throwable->map ex))})
                                (.flush ^Writer *err*)
                                true)))))
                      ;; If we can't read from the socket, exit the loop.
                      (catch #?(:bb clojure.lang.ExceptionInfo :clj clojure.lang.EdnReader$ReaderException) _ false)
                      (catch SocketException _ false)
                      ;; If the remote host closes the connection, exit the loop.
                      (catch IOException _ false))]
                (when recur? (recur)))))
          (finally
            (some-> debounce-service .shutdownNow)
            (.shutdownNow eval-service)
            (remove-tap tapfn)))))))

(defprotocol RPC
  (thread-bindings [this])
  (update-thread-bindings [this thread-bindings])
  (clear-thread-bindings [this])
  (host [this])
  (port [this])
  (write-out [this x])
  (write-err [this x])
  (close [this]))

(defn ^:private init-thread-bindings
  [bindings]
  (atom (merge {#'*ns* (the-ns 'user)} (select-keys bindings [#'*e #'*1 #'*2 #'*3 #'*warn-on-reflection*]))))

(defn open
  "Open an RPC server.

  RPC messages are EDN messages that look like nREPL ops. For example:

    {:op :load-base64 :blob \"...\" :file \"foo.clj\"}

  To add a new op, implement the tutkain.rpc/handle multimethod.

  Options:
    :port         The TCP port the server listens on.
    :bind-address The TCP bind address.

  Other options are subject to change.

  Returns an RPC instance."
  [{:keys [add-tap? bind-address port bindings xform-in xform-out]
      :or {add-tap? false bind-address "localhost" port 0 xform-in identity xform-out identity}}]
  (let [thread-bindings (init-thread-bindings bindings)
        out-writer (promise)
        err-writer (promise)
        server-name (format "tutkain/rpc-%s" (.incrementAndGet thread-counter))
        ^ServerSocket socket (server/start-server
                               {:address bind-address
                                :port port
                                :name server-name
                                :accept `accept
                                :args [{:add-tap? add-tap?
                                        :thread-bindings thread-bindings
                                        :eventual-out-writer out-writer
                                        :eventual-err-writer err-writer
                                        :xform-in #(xform-in %)
                                        :xform-out #(xform-out %)}]})]
    (reify RPC
      (thread-bindings [_] @thread-bindings)
      (clear-thread-bindings [_]
        (reset! thread-bindings nil))
      (update-thread-bindings [_ new-bindings]
        ;; Only set new thread bindings if there are no previously set thread
        ;; bindings.
        ;;
        ;; Thread bindings are unset after a successful REPL read and thread
        ;; binding determination to allow REPL to update the thread
        ;; bindings after the evaluation.
        ;;
        ;; This way, if a new set of thread bindings arrives while a previous
        ;; eval remains in progress, the REPL won't wipe the new bindings once
        ;; the ongoing eval completes.
        (swap! thread-bindings (fn [bindings] (if (nil? bindings) new-bindings bindings))))
      (host [_] (-> socket .getInetAddress .getHostName))
      (port [_] (.getLocalPort socket))
      (write-out [_ x] (@out-writer x))
      (write-err [_ x] (@err-writer x))
      (close [_] (server/stop-server server-name)))))

(defn default-init
  []
  (in-ns 'user)
  (apply require main/repl-requires))

(defn resolve-and-apply
  "Given two qualified symbols, if the first symbol resolves to a function,
  reload the namespace that function lives in. If it doesn't, require the
  function.

  If the symbol does not resolve to a function after requiring, return the
  function the second argument names."
  [sym fallback-sym]
  (assert (qualified-symbol? sym))

  (let [initf (try
                (if-some [s (resolve sym)]
                  (do (some-> sym core/namespace symbol (require :reload)) s)
                  (some-> sym requiring-resolve))
                (catch FileNotFoundException _
                  (requiring-resolve fallback-sym)))]
    (initf)))

(defn rpc
  [{:keys [init] :or {init `default-init} :as opts}]
  (try
    (let [eval-lock (Object.)]
      (resolve-and-apply init `default-init)
      (prn {:tag :out :val (str "Clojure " (clojure-version) " (Java " (Runtime/version) ")" "\n")})
      (accept
        (assoc opts
          :xform-in #(assoc % :eval-lock eval-lock)
          :thread-bindings (init-thread-bindings {})
          :eventual-out-writer (promise)
          :eventual-err-writer (promise))))
    (catch Exception ex
      (prn {:tag :err :val (with-out-str (pprint/pprint (Throwable->map ex) {:max-width 100 :map-entry-separator ""}))}))))
