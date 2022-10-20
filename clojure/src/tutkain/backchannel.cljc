(ns tutkain.backchannel
  (:require
   [clojure.core.server :as server]
   [clojure.edn :as edn]
   [tutkain.format :as format])
  (:import
   (clojure.lang LineNumberingPushbackReader RT)
   (java.nio.file LinkOption Files Paths Path)
   (java.io File IOException Writer)
   (java.net SocketException URL)
   (java.util.concurrent.atomic AtomicInteger)))

(comment (set! *warn-on-reflection* true) ,,,)

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
  #?(:bb nil
     :clj (when-let [^java.lang.reflect.Field field (.getDeclaredField LineNumberingPushbackReader "_columnNumber")]
            (-> field (doto (.setAccessible true)) (.set reader column)))))

(defn ^:private find-or-create-ns
  "Given a namespace symbol, if the namespace named by the symbol already
  exists, return it.

  Otherwise, create a new namespace named by the symbol and refer all public
  vars clojure.core into it."
  [ns]
  (or (some-> ns find-ns) (binding [*ns* (create-ns (or ns 'user))] (refer-clojure) *ns*)))

(defn ^:private make-path
  [& args]
  (Paths/get (first args) (into-array String (rest args))))

(def ^:private classpath-root-paths
  (delay
    (sequence
      (comp
        (map #(.getPath ^URL %))
        (remove #(.contains ^String % ".jar!"))
        (map #(make-path %)))
      (-> (RT/baseLoader) (.getResources "") (enumeration-seq)))))

(defn relative-to-classpath-root
  "Given a string path to a file, return the relative (to a classpath root) path
  to the file.

  If the file doesn't exist, return \"NO_SOURCE_PATH\"."
  [path-str]
  #?(:bb path-str
     :clj
     (if-some [^Path path (some-> path-str not-empty make-path)]
       (if (Files/exists path (into-array LinkOption []))
         (let [^Path path (.toRealPath path (into-array LinkOption []))]
           (if-some [^Path root (some #(when (.startsWith path ^Path %) %) @classpath-root-paths)]
             (str (.relativize root path))
             path-str))
         path-str)
       "NO_SOURCE_PATH")))

(defmethod handle :set-eval-context
  [{:keys [eval-context ^LineNumberingPushbackReader in ns file line column response]
    :or {line 0 column 0 response {}} :as message}]
  (.setLineNumber in (int line))
  (set-column! in (int column))
  (swap! eval-context
    #(cond-> %
       true (assoc :response response)
       true (assoc-in [:thread-bindings #'*file*] (relative-to-classpath-root file))
       ;; Babashka doesn't have *source-path*, but unlike in Clojure *file*
       ;; has the same effect.
       true (assoc-in [:thread-bindings #?(:bb #'*file* :clj #'*source-path*)] (or (some-> file File. .getName) "NO_SOURCE_FILE"))
       ns (assoc-in [:thread-bindings #'*ns*] (find-or-create-ns ns))))
  (respond-to message {:result :ok}))

(defmethod handle :interrupt
  [{:keys [^Thread repl-thread]}]
  (assert repl-thread)
  (.interrupt repl-thread))

(defonce ^:private ^AtomicInteger thread-counter
  (AtomicInteger.))

(defn accept
  [{:keys [bindings eventual-send-fn eval-context xform-in xform-out]
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
    (with-bindings bindings
      (try
        (binding [*out* (PrintWriter-on #(out-fn {:tag :out :val %1}) nil)
                  *err* (PrintWriter-on #(out-fn {:tag :err :val %1}) nil)]
          (loop []
            (let [recur?
                  (try
                    (let [message (edn/read {:eof ::EOF} *in*)]
                      (if (identical? ::EOF message)
                        false
                        (let [message (assoc (xform-in message) :eval-context eval-context :out-fn out-fn)]
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
          (remove-tap tapfn))))))

(defprotocol Backchannel
  (eval-context [this])
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
  [{:keys [bind-address port bindings xform-in xform-out]
      :or {bind-address "localhost" port 0 xform-in identity xform-out identity}}]
  (let [eval-context (atom {})
        eventual-send-fn (promise)
        server-name (format "tutkain/backchannel-%s" (.incrementAndGet thread-counter))
        socket (server/start-server
                 {:address bind-address
                  :port port
                  :name server-name
                  :accept `accept
                  :args [{:bindings (select-keys bindings [#'*e #'*1 #'*2 #'*3 #'*warn-on-reflection*])
                          :eval-context eval-context
                          :eventual-send-fn eventual-send-fn
                          :xform-in #(xform-in %)
                          :xform-out #(xform-out %)}]})]
    (reify Backchannel
      (eval-context [_] @eval-context)
      (update-thread-bindings [_ thread-bindings]
        (swap! eval-context update :thread-bindings merge
          (dissoc thread-bindings #'*file* #?(:bb nil :clj #'*source-path*) #'*ns*)))
      (host [_] (-> socket .getInetAddress .getHostName))
      (port [_] (.getLocalPort socket))
      (send-to-client [_ message] (@eventual-send-fn message))
      (close [_] (server/stop-server server-name)))))
