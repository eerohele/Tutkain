(ns tutkain.backchannel
  (:require
   [clojure.core.server :as server]
   [clojure.edn :as edn]
   [tutkain.format :as format])
  (:import
   (clojure.lang EdnReader$ReaderException LineNumberingPushbackReader)
   (java.io File IOException StringReader)
   (java.lang.reflect Field)
   (java.net SocketException)
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

(defn ^:private make-thread-bindings
  [{:keys [ns file]}]
  {#'*file* (or file "NO_SOURCE_PATH")
   #'*source-path* (or (some-> file File. .getName) "NO_SOURCE_FILE")
   #'*ns* (find-or-create-ns ns)})

(defmethod handle :set-eval-context
  [{:keys [^LineNumberingPushbackReader eval-context-queue in ns file line column]
    :or {line 0 column 0} :as message}]
  (.setLineNumber in (int line))
  (set-column! in (int column))
  (.put eval-context-queue {:thread-bindings (make-thread-bindings {:file file :ns ns})})
  (respond-to message {:result :ok}))



(defmethod handle :interrupt
  [{:keys [^Thread repl-thread eval-rpc-future]}]
  (assert repl-thread)
  (or (some-> eval-rpc-future deref future-cancel) (.interrupt repl-thread)))

(defmethod handle :eval
  [{:keys [eval-lock eval-context eval-rpc-future ns file line column code response]
    :or {line 0 column 0}
    :as message}]
  (reset! eval-rpc-future
    (future
      (with-bindings (merge
                       {#'*e nil
                        #'*1 nil
                        #'*2 nil
                        #'*3 nil}
                       (:thread-bindings @eval-context)
                       (make-thread-bindings {:file file :ns ns}))
        (try
          (with-open [reader (LineNumberingPushbackReader. (StringReader. code))]
            (run!
              (fn [form]
                (try
                  (let [ret (locking eval-lock (eval form))]
                    (set! *3 *2)
                    (set! *2 *1)
                    (set! *1 ret)
                    (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                    (respond-to message (assoc response :tag :ret :val (format/pp-str ret))))
                  (catch Throwable ex
                    (set! *e ex)
                    (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                    (respond-to message
                      (assoc response :tag :err
                        :val (format/Throwable->str ex)
                        :ns ns
                        :form form)))))
              (take-while #(not (identical? ::EOF %)) (repeatedly #(read {:eof ::EOF} reader)))))
          (catch Throwable ex
            (set! *e ex)
            (swap! eval-context assoc :thread-bindings (get-thread-bindings))
            (respond-to message
              (assoc response :tag :ret
                :val (format/pp-str (assoc (Throwable->map ex) :phase :read-source))
                :ns ns
                :exception true))))))))

(defonce ^:private ^AtomicInteger thread-counter
  (AtomicInteger.))

(defn accept
  [{:keys [eventual-send-fn xform-in xform-out]
    :or {xform-in identity xform-out identity}}]
  (let [out *out*
        lock (Object.)
        out-fn (fn [message]
                 (binding [*print-readably* true]
                   (locking lock
                     (.write out (pr-str (dissoc (xform-out message) :out-fn :eval-context)))
                     (.write out "\n")
                     (.flush out))))
        tapfn #(out-fn {:tag :tap :val (format/pp-str %1)})]
    (deliver eventual-send-fn out-fn)
    (add-tap tapfn)
    (try
      (binding [*out* (PrintWriter-on #(out-fn {:tag :out :val %1}) nil)]
        (loop []
          (let [recur?
                (try
                  (let [message (edn/read {:eof ::EOF} *in*)]
                    (if (identical? ::EOF message)
                      false
                      (let [message (assoc (xform-in message) :out-fn out-fn)]
                        (try
                          (handle message)
                          true
                          (catch Throwable ex
                            (respond-to message {:tag :ret
                                                 :exception true
                                                 :val (format/pp-str (Throwable->map ex))})
                            true)))))
                  ;; If we can't read from the socket, exit the loop.
                  (catch EdnReader$ReaderException _ false)
                  (catch SocketException _ false)
                  ;; If the remote host closes the connection, exit the loop.
                  (catch IOException _ false))]
            (when recur? (recur)))))
      (finally
        (remove-tap tapfn)))))

(defprotocol Backchannel
  (eval-context [this])
  (next-eval-context [this])
  (update-thread-bindings [this thread-bindings])
  (host [this])
  (port [this])
  (send-to-client [this message])
  (close [this]))

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

  Returns a Backchannel instance."
  [{:keys [bind-address port xform-in xform-out]
      :or {bind-address "localhost" port 0 xform-in identity xform-out identity}}]
  (let [eval-context (atom {})
        eval-rpc-future (atom nil)
        eval-context-queue (LinkedBlockingQueue. 128)
        eventual-send-fn (promise)
        server-name (format "tutkain/backchannel-%s" (.incrementAndGet thread-counter))
        socket (server/start-server
                 {:address bind-address
                  :port port
                  :name server-name
                  :accept `accept
                  :args [{:eventual-send-fn eventual-send-fn
                          :xform-in #(assoc (xform-in %)
                                       :eval-rpc-future eval-rpc-future
                                       :eval-context-queue eval-context-queue
                                       :eval-context eval-context)
                          :xform-out #(xform-out %)}]})]
    (reify Backchannel
      (eval-context [_] @eval-context)
      (next-eval-context [_] (.poll eval-context-queue))
      (update-thread-bindings [_ thread-bindings]
        (swap! eval-context assoc :thread-bindings thread-bindings))
      (host [_] (-> socket .getInetAddress .getHostName))
      (port [_] (.getLocalPort socket))
      (send-to-client [_ message] (@eventual-send-fn message))
      (close [_] (server/stop-server server-name)))))
