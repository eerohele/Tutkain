(ns tutkain.shadow
  (:require
   [clojure.core.async :as async]
   [shadow.cljs.devtools.api :as api]
   [shadow.cljs.devtools.server.repl-impl :as repl-impl]
   [shadow.cljs.devtools.server.supervisor :as supervisor]
   [tutkain.format :refer [Throwable->str]]
   [tutkain.backchannel :as backchannel])
  (:import
   (clojure.lang ExceptionInfo)))

(defn ^:private spec-for-runtime
  [out-fn runtime-id]
  {:init-state {:runtime-id runtime-id}

   :repl-prompt (constantly "")

   :repl-read-ex
   (fn [{:keys [read-result]} ex]
     (out-fn
       {:tag :err
        :val (Throwable->str ex)
        :form (:source read-result)}))

   :repl-result
   (fn [{:keys [ns read-result]} ret]
     (out-fn
       {:tag :ret
        :form (:source read-result)
        :ns (str ns)
        :val ret}))

   :repl-stderr
   (fn [{:keys [ns read-result]} text]
     (out-fn {:tag :err
              :ns (str ns)
              :val text
              :form (:source read-result)}))

   :repl-stdout
   (fn [_ text]
     (out-fn {:tag :out :val text}))})

(defn repl
  ([]
   (repl {}))
  ([opts]
   (let [lock (Object.)
         close-signal (async/promise-chan)
         out-fn #(binding [*flush-on-newline* true]
                   (locking lock
                     (prn %)))]
     (try
       (prn (sort (api/get-build-ids)))
       (let [build-id (read)
             backchannel (backchannel/open "tutkain.cljs/backchannel"
                           (assoc opts
                             :xform-in #(assoc % :build-id build-id :in *in*)
                             :xform-out #(dissoc % :in)))
             _ (prn {:host (-> backchannel .getLocalAddress .getHostName)
                     :port (-> backchannel .getLocalAddress .getPort)})
             {:keys [supervisor relay clj-runtime]} (api/get-runtime!)
             worker (supervisor/get-worker supervisor build-id)
             spec (spec-for-runtime out-fn (:client-id clj-runtime))]
         (repl-impl/do-repl worker relay *in* close-signal spec))
       (catch ExceptionInfo ex
         (prn {:tag :err :val (Throwable->str ex)}))
       (finally
         (async/>!! close-signal true))))))
