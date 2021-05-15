(ns tutkain.shadow
  (:require
   [clojure.core.async :as async]
   [clojure.core.server :as server]
   [shadow.cljs.devtools.api :as api]
   [shadow.cljs.devtools.server.runtime :as runtime]
   [shadow.cljs.devtools.server.repl-impl :as repl-impl]
   [shadow.cljs.devtools.server.supervisor :as supervisor]
   [tutkain.repl :refer [handle respond-to Throwable->str]])
  (:import
   (clojure.lang ExceptionInfo)))

(defmethod handle :shadow/choose-build-id
  [message]
  (respond-to message {:ids (sort (api/get-build-ids))}))

(defn ^:private spec-for-runtime
  [out-fn runtime-id]
  {:init-state {:runtime-id runtime-id}

   :repl-prompt (constantly "")

   :repl-read-ex
   (fn [_ ex]
     (out-fn
       {:tag :err
        :val (Throwable->str ex)}))

   :repl-result
   (fn [{:keys [ns read-result]} ret]
     (out-fn
       {:tag :ret
        :form (:source read-result)
        :ns (str ns)
        :val ret}))

   :repl-stderr
   (fn [_ text]
     (out-fn {:tag :err :val text}))

   :repl-stdout
   (fn [_ text]
     (out-fn {:tag :out :val text}))})

(defn ^:private build-id->server-name
  [build-id]
  (format "tutkain/shadow-cljs/%s" (name build-id)))

(defn repl
  "Given a Shadow CLJS worker, relay, and build ID, start a Shadow CLJS REPL.

  The REPL reads from *in* and prints to *out*.

  Can be used as the :accept arg of clojure.core.server/start-server."
  [worker relay build-id]
  (let [close-signal (async/promise-chan)
        lock (Object.)
        out-fn #(binding [*flush-on-newline* true]
                  (locking lock
                    (prn %)))
        ;; FIXME?
        runtime-id (some-> worker :state-ref deref :default-runtime-id)
        spec (spec-for-runtime out-fn runtime-id)]
    (try
      (repl-impl/do-repl worker relay *in* close-signal spec)
      (catch ExceptionInfo ex
        (prn {:tag :err :val (Throwable->str ex)}))
      (finally
        (async/>!! close-signal true)
        (server/stop-server (build-id->server-name build-id))))))

(defmethod handle :shadow/start-repl
  [{:keys [build-id port] :or {port 0} :as message}]
  (let [server-name (build-id->server-name build-id)]
    ;; TODO: If the user switches Shadow CLJS REPLs without disconnecting,
    ;; the server for the previous REPL will keep running. Clean up?
    (server/stop-server server-name)
    (if-some [{:keys [supervisor relay]} (runtime/get-instance)]
      (if-some [worker (supervisor/get-worker supervisor build-id)]
        (let [socket (server/start-server
                       {:name server-name
                        :port port
                        :accept `repl
                        :args [worker relay build-id]})]
          (respond-to message {:status :ok
                               :host (.. socket getInetAddress getHostName)
                               :port (.getLocalPort socket)}))
        (respond-to message {:status :fail :reason :no-worker}))
      (respond-to message {:status :fail :reason :no-server}))))

(defmethod handle :shadow/stop-repls
  [message]
  (let [stopped-ids (filter #(server/stop-server (build-id->server-name %))
                      (api/active-builds))]
    (respond-to message {:stopped-ids (set stopped-ids)})))
