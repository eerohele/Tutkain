(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint])
  (:import
   (clojure.lang Compiler Compiler$CompilerException LineNumberingPushbackReader)
   (java.io ByteArrayInputStream File InputStreamReader)
   (java.net InetSocketAddress)
   (java.nio.channels Channels ServerSocketChannel)
   (java.lang.reflect Field)
   (java.util Base64)))

(defn response-for
  [{:keys [id]} response]
  (cond-> response id (assoc :id id)))

(defmulti handle :op)

(defmethod handle :echo
  [{:keys [out-fn] :as message}]
  (out-fn message))

(defmethod handle :default
  [message]
  (throw (ex-info "Unknown op" {:message message})))

(defn ^:private base64-reader
  [blob]
  (->
    (Base64/getDecoder)
    (.decode blob)
    (ByteArrayInputStream.)
    (InputStreamReader.)
    (LineNumberingPushbackReader.)))

(defmethod handle :load-base64
  [{:keys [blob filename out-fn] :as message}]
  (with-open [reader (base64-reader blob)]
    (try
      (Compiler/load reader)
      (out-fn (response-for message {:filename filename :result :ok}))
      (catch Compiler$CompilerException _
        (out-fn (response-for message {:filename filename :result :fail}))))))

(defn pp-str
  [x]
  ;; ClojureScript eval results are strings
  ;;
  ;; TODO: Pretty-printing?
  (if (string? x)
    x
    (binding [pprint/*print-right-margin* 100]
      (-> x pprint/pprint with-out-str))))

(def eval-context
  (atom {:file nil :ns 'user}))

;; Borrowed from https://github.com/nrepl/nrepl/blob/8223894f6c46a2afd71398517d9b8fe91cdf715d/src/clojure/nrepl/middleware/interruptible_eval.clj#L32-L40
(defn- set-column!
  [^LineNumberingPushbackReader reader column]
  (when-let [field (->> LineNumberingPushbackReader
                     (.getDeclaredFields)
                     (filter #(= "_columnNumber" (.getName ^Field %)))
                     first)]
    (-> ^Field field
      (doto (.setAccessible true))
      (.set reader column))))

(defmethod handle :set-eval-context
  [{:keys [in ns file line column out-fn] :or {line 0 column 0} :as message}]
  (.setLineNumber in (int line))
  (set-column! in (int column))
  (->>
    (swap! eval-context assoc :file file :ns ns)
    (response-for message)
    out-fn))

(defn open-backchannel
  [{:keys [repl-in port] :or {port 0}}]
  (let [socket (ServerSocketChannel/open)
        address (InetSocketAddress. "localhost" port)
        repl-thread (Thread/currentThread)]
    (.bind socket address)
    (let [thread (Thread.
                   (fn []
                     (try
                       (let [socket-channel (.accept socket)
                             in (LineNumberingPushbackReader. (Channels/newReader socket-channel "UTF-8"))
                             out (Channels/newWriter socket-channel "UTF-8")
                             EOF (Object.)
                             out-fn (fn [message]
                                      (.write out (pr-str (dissoc message :out-fn :in)))
                                      (.write out "\n")
                                      (.flush out))]
                         (loop []
                           (when (.isOpen socket)
                             (let [message (read in false EOF)]
                               (when-not (identical? EOF message)
                                 (case (:op message)
                                   :interrupt (.interrupt repl-thread)
                                   (handle (assoc message :out-fn out-fn :in repl-in)))
                                 (recur))))))
                       (finally
                         (.close socket)))))]
      (doto thread
        (.setName "tutkain/backchannel")
        (.setDaemon true)
        (.start))
      socket)))

(def ^:dynamic ^:experimental *print*
  "A function you can use as the :print arg of clojure.main/repl.

  Prints evaluation results such that Tutkain can print them correctly."
  prn)

(def ^:dynamic ^:experimental *caught*
  "A function you can use as the :caught arg of clojure.main/repl.

  Prints exceptions such that Tutkain can print them correctly."
  main/repl-caught)

(defn repl
  [opts]
  (let [EOF (Object.)
        lock (Object.)
        out *out*
        out-fn (fn [message]
                 (binding [*out* out
                           *flush-on-newline* true
                           *print-readably* true]
                   (locking lock
                     (prn message))))
        tapfn #(out-fn {:tag :tap :val (pp-str %1)})
        backchannel (open-backchannel (assoc opts :repl-in *in*))]
    (main/with-bindings
      (in-ns 'user)
      (apply require main/repl-requires)
      (binding [*out* (PrintWriter-on #(out-fn {:tag :out :val %1}) nil)
                *err* (PrintWriter-on #(out-fn {:tag :err :val %1}) nil)
                *print* (fn [val & {:keys [ms form]}]
                          (out-fn (cond-> {:tag :ret
                                           :val (pp-str
                                                  (if (instance? Throwable val)
                                                    (Throwable->map val)
                                                    val))
                                           :ns (str (.name *ns*))}
                                    ms (assoc :ms ms)
                                    form (assoc :form form))))
                *caught* (fn [ex & {:keys [form]}]
                           (out-fn (cond-> {:tag :err
                                            :val (-> ex Throwable->map main/ex-triage main/ex-str)
                                            :ns (str (.name *ns*))}
                                     :form (assoc :form form))))]
        (try
          (out-fn {:tag :ret
                   :val (pr-str {:host (-> backchannel .getLocalAddress .getHostName)
                                 :port (-> backchannel .getLocalAddress .getPort)})})
          (add-tap tapfn)
          (loop []
            (when
              (try
                (let [[form s] (read+string {:eof EOF :read-cond :allow} *in*)]
                  (binding [*file* (or (some-> @eval-context :file) "NO_SOURCE_PATH")
                            *source-path* (or (some-> @eval-context :file File. .getName) "NO_SOURCE_FILE")]
                    (try
                      (when-not (identical? form EOF)
                        (eval
                          (let [ns-sym# (some->> @eval-context :ns)]
                            `(or (some->> '~ns-sym# find-ns ns-name in-ns) (ns ~ns-sym#))))
                        (let [start (System/nanoTime)
                              ret (eval form)
                              ms (quot (- (System/nanoTime) start) 1000000)]
                          (when-not (= :repl/quit ret)
                            (set! *3 *2)
                            (set! *2 *1)
                            (set! *1 ret)
                            (*print* ret :ms ms :form s)
                            true)))
                      (catch Throwable ex
                        (set! *e ex)
                        (*caught* ex :form s)
                        true))))
                (catch Throwable ex
                  (set! *e ex)
                  (out-fn {:tag :ret
                           :val (pp-str (assoc (Throwable->map ex) :phase :read-source))
                           :ns (str (.name *ns*))
                           :exception true})
                  true))
              (recur)))
          (finally
            (.close backchannel)
            (remove-tap tapfn)))))))
