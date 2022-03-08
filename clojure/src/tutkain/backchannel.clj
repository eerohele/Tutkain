(ns tutkain.backchannel
  (:require
   [clojure.edn :as edn]
   [tutkain.format :as format])
  (:import
   (clojure.lang LineNumberingPushbackReader)
   (java.io BufferedReader BufferedWriter File InputStreamReader OutputStreamWriter)
   (java.lang.reflect Field)
   (java.net InetAddress ServerSocket)
   (java.util.concurrent LinkedBlockingQueue)
   (java.util.concurrent.atomic AtomicInteger)))

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

;; Borrowed from https://github.com/nrepl/nrepl/blob/8223894f6c46a2afd71398517d9b8fe91cdf715d/src/clojure/nrepl/middleware/interruptible_eval.clj#L32-L40
(defn set-column!
  [^LineNumberingPushbackReader reader column]
  (when-let [field (.getDeclaredField LineNumberingPushbackReader "_columnNumber")]
    (-> ^Field field (doto (.setAccessible true)) (.set reader column))))

(defn ^:private find-or-create-ns
  "Given a namespace symbol, if the namespace named by the symbol already
  exists, return it.

  Otherwise, create a new namespace named by the symbol and refer all public
  vars clojure.core into it."
  [ns]
  (or (some-> ns find-ns) (binding [*ns* (create-ns (or ns 'user))] (refer-clojure) *ns*)))

(defmethod handle :set-eval-context
  [{:keys [^LineNumberingPushbackReader ctxq in ns file line column response]
    :or {line 0 column 0 response {}} :as message}]
  (.setLineNumber in (int line))
  (set-column! in (int column))
  (let [thread-bindings {#'*file* (or file "NO_SOURCE_PATH")
                         #'*source-path* (or (some-> file File. .getName) "NO_SOURCE_FILE")
                         #'*ns* (find-or-create-ns ns)}]
    (.put ctxq {:response response :thread-bindings thread-bindings})
    (respond-to message {:result :ok})))

(defmethod handle :interrupt
  [{:keys [^Thread repl-thread]}]
  (assert repl-thread)
  (.interrupt repl-thread))

(def ^:private ^AtomicInteger thread-counter
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

  Other options are subject to change.

  Returns a map with these keys:
    :socket                The ServerSocket instance this backchannel listens on.
    :send-over-backchannel A function you can call to send messages to the
                           client connected to this backchannel."
  [{:keys [port bind-address xform-in xform-out]
    :or {port 0 bind-address "localhost" xform-in identity xform-out identity}}]
  (let [address (InetAddress/getByName ^String bind-address)
        socket (ServerSocket. port 0 address)
        lock (Object.)
        eval-context (atom {:thread-bindings {#'*ns* (the-ns 'user)}})
        ctxq (LinkedBlockingQueue. 128)
        eventual-send-fn (promise)
        msg-loop (bound-fn []
                   (try
                     (let [conn (.accept socket)
                           in (-> conn .getInputStream InputStreamReader. BufferedReader. LineNumberingPushbackReader.)
                           out (-> conn .getOutputStream OutputStreamWriter. BufferedWriter.)
                           EOF (Object.)
                           out-fn (fn [message]
                                    (binding [*print-readably* true]
                                      (locking lock
                                        (.write out (pr-str (dissoc (xform-out message) :out-fn :eval-context)))
                                        (.write out "\n")
                                        (.flush out))))
                           tapfn #(out-fn {:tag :tap :val (format/pp-str %1)})]
                       (deliver eventual-send-fn out-fn)
                       (add-tap tapfn)
                       (binding [*out* (PrintWriter-on #(out-fn {:tag :out :val %1}) nil)]
                         (try
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
                                                  (let [message (assoc (xform-in message)
                                                                  :eval-context eval-context
                                                                  :ctxq ctxq
                                                                  :out-fn out-fn)]
                                                    (try
                                                      (handle message)
                                                      true
                                                      (catch Throwable ex
                                                        (respond-to message {:tag :ret
                                                                             :exception true
                                                                             :val (format/pp-str (Throwable->map ex))})
                                                        true))))]
                                     (when recur? (recur)))))))
                           (finally
                             (remove-tap tapfn)))))
                     (finally
                       (.close socket))))
        thread (Thread. ^Runnable msg-loop)]
    (doto thread
      (.setName (format "tutkain/backchannel-%s" (.incrementAndGet thread-counter)))
      (.setDaemon true)
      (.start))
    {:eval-context eval-context
     :ctxq ctxq
     :socket socket
     :send-over-backchannel (fn [message] (@eventual-send-fn message))}))
