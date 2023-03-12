(ns tutkain.shadow
  (:require
   [clojure.core.async :as async]
   [clojure.pprint :as pprint]
   [cljs.util :refer [*clojurescript-version*]]
   [shadow.cljs.devtools.api :as api]
   [shadow.cljs.devtools.server.supervisor :as supervisor]
   [shadow.remote.relay.api :as relay]
   [tutkain.backchannel :as backchannel :refer [respond-to]]
   [tutkain.format :refer [pp-str]])
  (:import (java.net SocketException)))

(defn print-result
  [result]
  (binding [*flush-on-newline* true
            *default-data-reader-fn* tagged-literal
            *read-eval* false]
    (try
      (pprint/pprint
        (some-> result read-string))
      (catch Throwable _
        (println result)))))

(def ^:private no-runtime-err
  "⋯ No JavaScript runtime connected to shadow-cljs process. ⋯

Connect a JavaScript runtime (for example, Node.js or a browser) to the shadow-cljs process and try
again.

For more information on connecting a JavaScript runtime, see:

https://shadow-cljs.github.io/docs/UsersGuide.html#repl-troubleshooting.
")

(defmethod backchannel/evaluate :cljs
  [{:keys [to-relay runtime-id ret-chan ns code file line column]
    :or {file "NO_SOURCE_FILE" line 1 column 1}
    :as message}]
  (if-some [runtime-id @runtime-id]
    (do
      (async/go (respond-to message (async/<! ret-chan)))
      (async/>!! to-relay
        {:op :cljs-eval
         :to runtime-id
         :input {:code code
                 ;; Not sure whether :file, :line, and :column have any effect. Probably not.
                 :file file
                 :line line
                 :column column
                 :ns (or (some-> ns symbol) 'cljs.user)}}))
    (respond-to message {:tag :err :val no-runtime-err})))

(defmulti handle :op)

(defmethod handle :eval-result-ref
  [{:keys [tag to-relay from ref-oid]}]
  (reset! tag :ret)
  (async/>!! to-relay {:op :obj-edn :to from :oid ref-oid}))

(defmethod handle :eval-runtime-error
  [{:keys [tag to-relay from ex-oid]}]
  (reset! tag :err)
  (async/>!! to-relay
    {:op :obj-ex-str
     :to from
     :oid ex-oid}))

(defmethod handle :eval-compile-error
  [{:keys [ret-chan report]}]
  (async/>!! ret-chan {:tag :err :val report}))

;; e.g. (/ :a)
(defmethod handle :eval-compile-warnings
  [{:keys [ret-chan warnings]}]
  ;; FIXME: Send warnings as separate responses; can't now, because we only support sending a single response
  (async/>!! ret-chan {:tag :err :val (pp-str warnings)}))

(defmethod handle :obj-result
  [{:keys [tag ret-chan result]}]
  ;; TODO: This doesn't seem quite right.
  (if (= @tag :err)
    (async/>!! ret-chan
      {:tag :err
       :val result})
    (async/>!! ret-chan
      {:tag :ret
       :val (with-out-str (print-result result))})))

(defmethod handle :runtime-print
  [{:keys [stream text]}]
  (case stream :stdout
    (prn {:tag :out :val text})
    (binding [*err* *out*]
      (prn {:tag :err :val text}))))

(defmethod handle :client-not-found
  [_]
  (prn {:tag :err :val no-runtime-err}))

(defmethod handle ::notification
  [{:keys [runtime-id to-relay client-id event-op]}]
  ;; TODO: Make these status bar statuses instead?
  (case event-op
    :client-connect
    (do
      (async/>!! to-relay {:op :request-notify :notify-op ::notification})
      (async/>!! to-relay {:op :runtime-print-sub :to client-id})
      (reset! runtime-id client-id)
      (prn {:tag :out :val "⚡ JavaScript runtime connected, ready to evaluate.\n"}))

    :client-disconnect
    (prn {:tag :err :val no-runtime-err})

    nil))

(defmethod handle :welcome [_] _)

(defmethod handle :default
  [message]
  (throw (ex-info "No handler for message" {:message message})))

(defn init
  [build-id]
  (let [{:keys [supervisor relay]} (api/get-runtime!)
        {:keys [proc-id state-ref clj-runtime] :as worker} (supervisor/get-worker supervisor build-id)]
    (if-not worker
      (prn {:tag :err :val (format "ERR: No shadow-cljs watch running for build ID %s.\n" build-id)})
      (let [to-relay (async/chan 10)
            from-relay (async/chan 256)
            connection-stop (relay/connect relay to-relay from-relay {})
            _ (async/<!! from-relay)
            _ (async/>!! to-relay {:op :hello :client-info {:build-id build-id :proc-id proc-id}})
            runtime-id (atom (or (:client-id clj-runtime) (some-> state-ref deref :default-runtime-id)))
            _ (async/>!! to-relay {:op :request-notify :notify-op ::notification})
            ctrl-chan (async/promise-chan)
            ret-chan (async/chan 1)
            tag (atom :ret)]
        (async/thread
          (try
            (loop []
              (let [[val chan] (async/alts!! [ctrl-chan from-relay])]
                (when (= chan from-relay)
                  (handle (merge {:runtime-id runtime-id
                                  :tag tag
                                  :ret-chan ret-chan
                                  :to-relay to-relay
                                  :from-relay from-relay} val))
                  (recur))))
            (catch SocketException _)
            (finally
              (async/close! connection-stop))))

        (let [{:keys [major minor qualifier]} *clojurescript-version*]
          (prn {:tag :out :val (format "ClojureScript %s.%s.%s\n" major minor qualifier)}))

        {:tag tag
         :ret-chan ret-chan
         :to-relay to-relay
         :from-relay from-relay
         :runtime-id runtime-id
         :quit-fn (fn [] (async/>!! ctrl-chan ::quit))}))))

(defn rpc
  [{:keys [build-id] :as opts}]
  (when-some [ret (init build-id)]
    (let [{:keys [tag ret-chan runtime-id to-relay]} ret]
      (backchannel/accept
        (assoc opts
          :greet? false
          :thread-bindings (atom {})
          :eventual-out-writer (promise)
          :eventual-err-writer (promise)
          :xform-in #(assoc %
                       :tag tag
                       :build-id build-id
                       :ret-chan ret-chan
                       :runtime-id runtime-id
                       :to-relay to-relay)
          :xform-out #(dissoc % :ret-chan :to-relay))))))

(comment
  (rpc {:build-id :node-script})

  {:id 1 :op :eval :code "(inc 2)" :dialect :cljs}
  {:id 1 :op :eval :code "(inc 2" :dialect :cljs}
  {:id 1 :op :eval :code "(println 1)" :dialect :cljs}
  {:id 1 :op :eval :code "(merge 1 2)" :dialect :cljs}
  {:op :echo}
  {:op :quit}
  ,,,)
