(ns tutkain.repl.runtime.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint])
  (:import
   (clojure.lang Compiler Compiler$CompilerException LineNumberingPushbackReader)
   (java.io ByteArrayInputStream InputStreamReader)
   (java.net InetSocketAddress)
   (java.nio.channels Channels ServerSocketChannel)
   (java.util Base64)))

(defn response-for
  [{:keys [id]} response]
  (cond-> response id (assoc :id id)))

(defmulti handle :op)

(defmethod handle :echo
  [{:keys [out-fn] :as message}]
  (out-fn (dissoc message :out-fn)))

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
  (binding [pprint/*print-right-margin* 100]
    (-> x pprint/pprint with-out-str)))

(defonce current-ns
  (atom 'user))

(defmethod handle :switch-ns
  [{:keys [ns out-fn] :as message}]
  (out-fn (response-for message {:ns (reset! current-ns ns)})))

(defn open-backchannel
  [{:keys [port] :or {port 0}}]
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
                                      (.write out (pr-str message))
                                      (.write out "\n")
                                      (.flush out))]
                         (loop []
                           (when (.isOpen socket)
                             (let [message (read in false EOF)]
                               (when-not (identical? EOF message)
                                 (case (:op message)
                                   :interrupt (.interrupt repl-thread)
                                   (handle (assoc message :out-fn out-fn)))
                                 (recur))))))
                       (finally
                         (.close socket)))))]
      (doto thread
        (.setName "tutkain/backchannel")
        (.setDaemon true)
        (.start))
      socket)))

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
        backchannel (open-backchannel opts)]
    (main/with-bindings
      (in-ns 'user)
      (apply require main/repl-requires)
      (binding [*out* (PrintWriter-on #(out-fn {:tag :out :val %1}) nil)
                *err* (PrintWriter-on #(out-fn {:tag :err :val %1}) nil)]
        (try
          (out-fn {:tag :ret
                   :val (pr-str {:host (-> backchannel .getLocalAddress .getHostName)
                                 :port (-> backchannel .getLocalAddress .getPort)})})
          (add-tap tapfn)
          (loop []
            (when (try
                    (let [[form s] (read+string {:eof EOF :read-cond :allow} *in*)]
                      (try
                        (when-not (identical? form EOF)
                          (eval
                            (let [ns-sym# @current-ns]
                              `(or (some->> '~ns-sym# find-ns ns-name in-ns) (ns ~ns-sym#))))
                          (let [start (System/nanoTime)
                                ret (eval form)
                                ms (quot (- (System/nanoTime) start) 1000000)]
                            (when-not (= :repl/quit ret)
                              (set! *3 *2)
                              (set! *2 *1)
                              (set! *1 ret)
                              (out-fn {:tag :ret
                                       :val (pp-str
                                              (if (instance? Throwable ret)
                                                (Throwable->map ret)
                                                ret))
                                       :ns (str (reset! current-ns (.name *ns*)))
                                       :ms ms
                                       :form s})
                              true)))
                        (catch Throwable ex
                          (set! *e ex)
                          (out-fn {:tag :err
                                   :val (-> ex Throwable->map main/ex-triage main/ex-str)
                                   :ns (str (reset! current-ns (.name *ns*)))
                                   :form s})
                          true)))
                    (catch Throwable ex
                      (set! *e ex)
                      (out-fn {:tag :ret
                               :val (pp-str (assoc (Throwable->map ex) :phase :read-source))
                               :ns (str (reset! current-ns (.name *ns*)))
                               :exception true})
                      true))
              (recur)))
          (finally
            (.close backchannel)
            (remove-tap tapfn)))))))
