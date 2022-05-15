(ns tutkain.shadow
  (:require
   [clojure.core.async :as async]
   [clojure.pprint :as pprint]
   [clojure.tools.reader.reader-types :as readers]
   [clojure.tools.reader :as reader]
   [cljs.analyzer :as analyzer]
   [cljs.util :refer [*clojurescript-version*]]
   [shadow.cljs.devtools.api :as api]
   [shadow.cljs.devtools.server.supervisor :as supervisor]
   [shadow.cljs.devtools.server.worker :as worker]
   [shadow.remote.relay.api :as relay]
   [tutkain.format :as format]
   [tutkain.backchannel :as backchannel])
  (:import
   (clojure.lang ExceptionInfo)
   (java.util.concurrent Executors TimeUnit ThreadPoolExecutor$CallerRunsPolicy)))

(defn ^:private read-one
  [backchannel build-state reader]
  (try
    ;; FIXME: NO_SOURCE_FILE, use *source-path* from backchannel eval context?
    (let [in (readers/source-logging-push-back-reader reader 1 "NO_SOURCE_FILE")
          _ (readers/unread in (readers/read-char in))
          eof (Object.)
          reader-opts {:eof eof :read-cond :allow :features #{:cljs}}
          eval-context (backchannel/next-eval-context backchannel)
          current-ns (or
                       (some-> eval-context :thread-bindings (get #'clojure.core/*ns*) ns-name)
                       (get-in build-state [:repl-state :current-ns] 'user))
          build-id (:shadow.build/build-id build-state)
          compiler-env (api/compiler-env build-id)
          [form s] (binding [*ns* (create-ns current-ns)
                             reader/*alias-map* (apply merge
                                                  ((juxt :requires :require-macros)
                                                   (analyzer/get-namespace (delay compiler-env) current-ns)))
                             reader/*data-readers* {}
                             reader/*default-data-reader-fn* (fn [_ val] val)
                             reader/resolve-symbol identity]
                     (reader/read+string reader-opts in))
          ;; Without this, the next thing we read is a sole \newline for some
          ;; reason.
          _ (readers/read-char in)
          eof? (identical? form eof)]
      (-> {:eof? eof?} (cond->
                         (not eof?) (assoc :form form :source s :ns (ns-name current-ns))
                         (and (not eof?) eval-context) (assoc :eval-context eval-context))))
    (catch Exception ex
      {:error? true
       :ex ex})))

;; Vendored from shadow-cljs[1] to avoid using impl namespace.
;;
;; Modified to add ns aliases and to remove calls to some possibly internal
;; logging namespaces.
;;
;; Original code copyright © 2020 Thomas Heller.
;;
;; Distributed under the Eclipse Public License either version 1.0 or (at your
;; option) any later version.
;;
;; [1]: https://github.com/thheller/shadow-cljs/blob/22c3f41f86a5ba4754eb774da9c03ec91043d897/src/main/shadow/cljs/devtools/server/repl_impl.clj#L19-L318
(defn do-repl
  [{:keys [proc-stop] :as worker}
   relay
   reader
   close-signal
   {:keys [init-state
           repl-prompt
           repl-read-ex
           repl-result
           repl-stdout
           repl-stderr]}
   backchannel]
  {:pre [(some? worker)
         (some? proc-stop)
         (some? close-signal)]}

  (let [to-relay
        (async/chan 10)

        from-relay
        (async/chan 256)

        _
        (relay/connect relay to-relay from-relay {})

        {:keys [client-id]}
        (async/<!! from-relay)

        stdin
        (async/chan)

        _
        (async/>!! to-relay
          {:op :hello
           :client-info {:type :repl-session
                         :build-id (:build-id worker)
                         :proc-id (:proc-id worker)}})

        proc-stdio-available?
        (get-in worker [:cli-opts ::node-repl])

        proc-stdio
        (async/chan
          (async/sliding-buffer 100)
          (filter #(contains? #{:proc/stdout :proc/stderr} (:type %))))

        read-lock
        (async/chan)


        init-ns
        (or (:ns init-state)
          (some-> worker :state-ref deref :build-config :devtools :repl-init-ns)
          'cljs.user)

        repl-timeout
        (or (some-> worker :state-ref deref :build-config :devtools :repl-timeout) 30000)

        init-state
        (assoc init-state
          :ns init-ns
          :stage :read
          :client-id client-id)]

    (when proc-stdio-available?
      (worker/watch worker proc-stdio))

    ;; read loop, blocking IO
    ;; cannot block main loop or we'll never receive async events
    (async/thread
      (try
        (loop []
          ;; wait until told to read
          (when (some? (async/<!! read-lock))
            (let [{:keys [eof?] :as next} (read-one backchannel (some-> worker :state-ref deref :build-state) reader)]
              (if eof?
                (async/close! stdin)
                ;; don't recur in case stdin was closed while in blocking read
                (when (async/>!! stdin next)
                  (recur))))))
        (catch Exception e
          (println e)))
      (async/close! stdin))

    (async/>!! read-lock 1)

    ;; initial prompt
    (repl-prompt init-state)

    (let [result
          (loop [repl-state init-state]
            (async/alt!!
              proc-stop
              ([_] ::worker-stop)

              close-signal
              ([_] ::close-signal)

              stdin
              ([read-result]
               ;; (tap> [:repl-from-stdin read-result repl-state])
               (when (some? read-result)
                 (let [{:keys [eof? error? ex source]} read-result]
                   (cond
                     eof?
                     :eof

                     error?
                     (do (repl-read-ex repl-state ex)
                       (recur repl-state))

                     (= ":repl/quit" source)
                     :repl/quit

                     (= ":cljs/quit" source)
                     :cljs/quit

                     :else
                     (let [runtime-id
                           (or (:runtime-id repl-state)
                             ;; no previously picked runtime, pick new one from worker when available
                             (when-some [runtime-id (-> worker :state-ref deref :default-runtime-id)]
                               ;; don't capture client side prints when
                               ;; already getting proc/stdout|err from worker
                               ;; only available when managing the actual process (eg. node-repl)
                               (when-not proc-stdio-available?
                                 (async/>!! to-relay {:op :runtime-print-sub
                                                      :to runtime-id}))
                               (async/>!! to-relay {:op :request-notify
                                                    :notify-op ::runtime-disconnect
                                                    :query [:eq :client-id runtime-id]})
                               runtime-id))]

                       (if-not runtime-id
                         (do (repl-stderr repl-state "No available JS runtime.\nSee https://shadow-cljs.github.io/docs/UsersGuide.html#repl-troubleshooting")
                           (repl-result repl-state nil)
                           (repl-prompt repl-state)
                           (async/>!! read-lock 1)
                           (recur repl-state))

                         (let [msg {:op :cljs-eval
                                    :to runtime-id
                                    :input {:code source
                                            :ns (:ns read-result (:ns repl-state))
                                            :repl true}}]

                           (async/>!! to-relay msg)
                           (-> repl-state
                             (assoc :stage :eval :runtime-id runtime-id :read-result read-result)
                             (recur)))))))))

              from-relay
              ([msg]
               ;; (tap> [:repl-from-relay msg repl-state])
               (when (some? msg)
                 (case (:op msg)
                   (::runtime-disconnect :client-not-found)
                   (do (repl-stderr repl-state "The previously used runtime disappeared. Will attempt to pick a new one when available but your state might be gone.\n")
                     (repl-prompt repl-state)
                     ;; may be in blocking read so read-lock is full
                     ;; must not use >!! since that would deadlock
                     ;; only offer! and discard when not in blocking read anyways
                     (async/offer! read-lock 1)
                     (-> repl-state
                       (dissoc :runtime-id)
                       (recur)))

                   :eval-result-ref
                   (let [{:keys [from ref-oid eval-ns]} msg]

                     (async/>!! to-relay
                       {:op :obj-request
                        :to from
                        :request-op :edn
                        :oid ref-oid})

                     (-> repl-state
                       (assoc :ns eval-ns
                         :stage :print
                         :eval-result msg)
                       (recur)))

                   :obj-request-failed
                   (let [{:keys [from ex-oid]} msg]
                     (if (:print-failed repl-state)
                       (do (repl-stderr repl-state "The result failed to print and printing the exception also failed. No clue whats going on.")
                         (repl-prompt repl-state)
                         (async/>!! read-lock 1)
                         (-> repl-state
                           (dissoc :print-failed)
                           (recur)))

                       (do (async/>!! to-relay
                             {:op :obj-request
                              :to from
                              :request-op :str
                              :oid ex-oid})

                         (-> repl-state
                           (assoc :print-failed true)
                           (recur)))))

                   :obj-result
                   (let [{:keys [result]} msg]
                     (cond
                       (= :error (:stage repl-state))
                       (do (repl-stderr repl-state (str "\n" result))
                         ;; FIXME: should there be an actual result? looks annoying on the streaming REPLs
                         ;; this was only here for nREPL right?
                         (repl-result repl-state ":repl/exception!"))

                       (not (:print-failed repl-state))
                       (repl-result repl-state result)

                       :else
                       (do (repl-stderr repl-state "The result object failed to print. It is available via *1 if you want to interact with it.\n")
                         (repl-stderr repl-state "The exception was: \n")
                         (repl-stderr repl-state (str result "\n"))
                         (repl-result repl-state ":repl/print-error!")))

                     (repl-prompt repl-state)

                     (async/>!! read-lock 1)
                     (-> repl-state
                       (assoc :stage :read)
                       (dissoc :print-failed)
                       (recur)))

                   :eval-compile-warnings
                   (let [{:keys [warnings]} msg]
                     (doseq [warning warnings]
                       (repl-stderr repl-state
                         ;; FIXME: cf. https://github.com/thheller/shadow-cljs/blob/22c3f41f86a5ba4754eb774da9c03ec91043d897/src/main/shadow/cljs/devtools/server/repl_impl.clj#L250-L253
                         (pr-str (assoc warning :resource-name "<eval>"))))
                     (repl-result repl-state nil)
                     (repl-prompt repl-state)
                     (async/>!! read-lock 1)
                     (recur (assoc repl-state :stage :read)))

                   :eval-compile-error
                   (let [{:keys [report]} msg]
                     (repl-stderr repl-state (str report "\n"))
                     (repl-result repl-state nil)
                     (repl-prompt repl-state)
                     (async/>!! read-lock 1)
                     (recur (assoc repl-state :stage :read)))

                   :eval-runtime-error
                   (let [{:keys [from ex-oid]} msg]
                     (async/>!! to-relay
                       {:op :obj-request
                        :to from
                        :request-op :ex-str
                        :oid ex-oid})
                     (recur (assoc repl-state :stage :error)))

                   :runtime-print
                   (let [{:keys [stream text]} msg]
                     (case stream
                       :stdout
                       (repl-stdout repl-state text)
                       :stderr
                       (repl-stderr repl-state text))
                     (recur repl-state))

                   (do (tap> [:unexpected-from-relay msg repl-state worker relay])
                     (repl-stderr "INTERNAL REPL ERROR: Got an unexpected reply from relay, check Inspect")
                     (recur repl-state)))))

              proc-stdio
              ([msg]
               (when (some? msg)
                 (let [{:keys [type text]} msg]
                   (case type
                     :proc/stdout
                     (repl-stdout repl-state text)
                     :proc/stderr
                     (repl-stderr repl-state text))

                   (recur repl-state))))

              (async/timeout repl-timeout)
              ([_]
               ;; fine to wait long time while reading
               (if (= :read (:stage repl-state))
                 (recur repl-state)
                 ;; should time out eventually while waiting for eval/print so you can retry
                 (do (async/>!! read-lock 1)
                   (repl-stderr repl-state (str "Timeout while waiting for result.\n"))
                   (-> repl-state
                     (assoc :stage :read)
                     (recur)))))))]

      (async/close! to-relay)
      (async/close! read-lock)
      (async/close! proc-stdio)
      (async/close! stdin)

      result)))

(defn print-result
  [lock result]
  (binding [*flush-on-newline* true
            *default-data-reader-fn* tagged-literal
            *read-eval* false]
     (locking lock
       (try
         (pprint/pprint
           (some-> result read-string))
         (catch Throwable _
           (println result))))))

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

(defn repl
  ([]
   (repl {}))
  ([{:keys [build-id] :as opts}]
   (let [lock (Object.)
         close-signal (async/promise-chan)
         out-fn (partial print-result lock)
         debounce-service (doto (Executors/newScheduledThreadPool 1)
                            (.setRejectedExecutionHandler (ThreadPoolExecutor$CallerRunsPolicy.)))
         debounce (make-debouncer debounce-service)
         backchannel (backchannel/open
                       (assoc opts
                         :xform-in #(assoc % :build-id build-id :in *in*)
                         :xform-out #(dissoc % :in)))
         out-writer (PrintWriter-on #(backchannel/send-to-client backchannel {:tag :out :val %1}) nil)
         err-writer (PrintWriter-on #(backchannel/send-to-client backchannel {:tag :err :val %1}) nil)
         flush-out (debounce #(.flush out-writer) 50)
         flush-err (debounce #(.flush err-writer) 50)
         write-out (fn [string] (.write out-writer string) (flush-out))
         write-err (fn [string] (.write err-writer string) (flush-err))
         out (PrintWriter-on write-out #(.close out-writer))
         err (PrintWriter-on write-err #(.close err-writer))]
     (try
       (let [_ (prn {:greeting (let [{:keys [major minor qualifier]} *clojurescript-version*]
                                 (format "ClojureScript %s.%s.%s\n" major minor qualifier))
                     :host (backchannel/host backchannel)
                     :port (backchannel/port backchannel)})
             {:keys [supervisor relay clj-runtime]} (api/get-runtime!)
             worker (supervisor/get-worker supervisor build-id)]
         (do-repl worker relay *in* close-signal
           {:init-state {:runtime-id (:client-id clj-runtime)}

            :repl-prompt (constantly "")

            :repl-read-ex
            (fn [{:keys [read-result]} ex]
              (backchannel/send-to-client backchannel
                {:tag :err
                 :val (format/Throwable->str ex)
                 :form (:source read-result)}))

            :repl-result
            (fn [{:keys [read-result]} ret]
              (let [response (:response (:eval-context read-result))]
                (if (#{:inline :clipboard} (:output response))
                  (backchannel/send-to-client backchannel (assoc response :tag :ret :val (with-out-str (print-result lock ret))))
                  (out-fn ret))))

            :repl-val
            (fn [_ ret]
              (backchannel/send-to-client backchannel
                {:tag :ret
                 :val ret}))

            :repl-stderr
            (fn [_ text]
              (.write err (str (.trim text) "\n"))
              (.flush err))

            :repl-stdout
            (fn [_ text]
              (.write out text)
              (.flush out))}
           backchannel))
       (catch ExceptionInfo ex
         (backchannel/send-to-client backchannel {:tag :err :val (format/Throwable->str ex)}))
       (catch AssertionError ex
         (backchannel/send-to-client backchannel {:tag :err :val (format/Throwable->str ex)}))
       (finally
         (async/>!! close-signal true)
         (.shutdown debounce-service)
         (backchannel/close backchannel))))))
