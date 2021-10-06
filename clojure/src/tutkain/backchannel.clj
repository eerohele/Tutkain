(ns tutkain.backchannel
  (:require
   [clojure.edn :as edn]
   [tutkain.format :as format])
  (:import
   (clojure.lang Compiler Compiler$CompilerException LineNumberingPushbackReader)
   (java.io BufferedReader BufferedWriter ByteArrayInputStream InputStreamReader OutputStreamWriter FileNotFoundException)
   (java.lang.reflect Field)
   (java.net InetSocketAddress)
   (java.net InetAddress ServerSocket)
   (java.util.concurrent.atomic AtomicInteger)
   (java.util Base64)))

(defn respond-to
  "Respond to a backchannel op message."
  [{:keys [id out-fn]} response]
  (out-fn (cond-> response id (assoc :id id))))

(defmulti handle
  "Handle a backchannel op message.

  Dispatches on :op."
  :op)

(defmethod handle :echo
  [message]
  (respond-to message {:op :echo}))

(defmethod handle :default
  [message]
  (throw (ex-info "Unknown op" {:message message})))

(def ^:private base64-decoder
  (Base64/getDecoder))

(defn base64-reader
  [blob]
  (->
    base64-decoder
    (.decode blob)
    (ByteArrayInputStream.)
    (InputStreamReader.)
    (LineNumberingPushbackReader.)))

(defmethod handle :load-base64
  [{:keys [blob path filename requires] :as message}]
  (try
    (some->> requires (run! require))
    (with-open [reader (base64-reader blob)]
      (try
        (Compiler/load reader path filename)
        (respond-to message {:filename filename :result :ok})
        (catch Compiler$CompilerException ex
          (respond-to message {:filename filename :result :fail :reason :compiler-ex :ex (Throwable->map ex)}))))
    (catch FileNotFoundException ex
      (respond-to message {:filename filename :result :fail :reason :not-found :ex (Throwable->map ex)}))))

(def eval-context
  (atom {:file nil :line 0 :column 0}))

;; Borrowed from https://github.com/nrepl/nrepl/blob/8223894f6c46a2afd71398517d9b8fe91cdf715d/src/clojure/nrepl/middleware/interruptible_eval.clj#L32-L40
(defn set-column!
  [^LineNumberingPushbackReader reader column]
  (when-let [field (.getDeclaredField LineNumberingPushbackReader "_columnNumber")]
    (-> ^Field field (doto (.setAccessible true)) (.set reader column))))

(defmethod handle :set-eval-context
  [{:keys [in file line column] :or {line 0 column 0} :as message}]
  (.setLineNumber in (int line))
  (set-column! in (int column))
  (let [new-context (swap! eval-context assoc :file file :line line :column column)]
    (respond-to message new-context)))

(defmethod handle :interrupt
  [{:keys [repl-thread]}]
  (assert repl-thread)
  (.interrupt repl-thread))

(def ^:private thread-counter
  (AtomicInteger.))

(defn open
  "Open a backchannel that listens for editor tooling messages on a socket.

  Editor tooling messages are EDN messages that look like nREPL ops. For
  example:

    {:op :load-base64 :blob \"...\" :file \"foo.clj\"}

  To add a new op, implement the tutkain.backchannel/handle multimethod.

  Options:
    :port         The TCP port the backchannel listens on.
    :bind-address The TCP bind address.

  Other options are subject to change."
  [{:keys [port bind-address xform-in xform-out]
    :or {port 0 bind-address "localhost" xform-in identity xform-out identity}}]
  (let [address (InetAddress/getByName ^String bind-address)
        socket (ServerSocket. port 0 address)
        lock (Object.)
        thread (Thread.
                 (bound-fn []
                   (try
                     (let [conn (.accept socket)
                           in (-> conn .getInputStream InputStreamReader. BufferedReader. LineNumberingPushbackReader.)
                           out (-> conn .getOutputStream OutputStreamWriter. BufferedWriter.)
                           EOF (Object.)
                           out-fn (fn [message]
                                    (locking lock
                                      (.write out (pr-str (dissoc (xform-out message) :out-fn)))
                                      (.write out "\n")
                                      (.flush out)))]
                       (loop []
                         (when-not (.isClosed socket)
                           (when-some [message (try
                                                 (edn/read {:eof EOF} in)
                                                 ;; If we can't read from the socket, exit the loop.
                                                 (catch java.net.SocketException _)
                                                 ;; If the remote host closes the connection, exit the loop.
                                                 (catch java.io.IOException _))]
                             (when-not (identical? EOF message)
                               (let [recur? (case (:op message)
                                              :quit false
                                              (let [message (assoc (xform-in message) :out-fn out-fn)]
                                                (try
                                                  (handle message)
                                                  true
                                                  (catch Throwable ex
                                                    (respond-to message {:tag :ret
                                                                         :exception true
                                                                         :val (format/pp-str (Throwable->map ex))})
                                                    true))))]
                                 (when recur? (recur))))))))
                     (finally
                       (.close socket)))))]
    (doto thread
      (.setName (format "tutkain/backchannel-%s" (.incrementAndGet thread-counter)))
      (.setDaemon true)
      (.start))
    socket))
