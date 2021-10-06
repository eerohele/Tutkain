(ns tutkain.shadow
  (:require
   [clojure.core.async :as async]
   [clojure.pprint :as pprint]
   [cljs.util :refer [*clojurescript-version*]]
   [shadow.cljs.devtools.api :as api]
   [shadow.cljs.devtools.server.repl-impl :as repl-impl]
   [shadow.cljs.devtools.server.supervisor :as supervisor]
   [tutkain.format :refer [Throwable->str]]
   [tutkain.backchannel :as backchannel])
  (:import
   (clojure.lang ExceptionInfo)))

(defn ^:private spec-for-runtime
  [out-fn send-over-backchannel runtime-id]
  {:init-state {:runtime-id runtime-id}

   :repl-prompt (constantly "")

   :repl-read-ex
   (fn [{:keys [read-result]} ex]
     (send-over-backchannel
       {:tag :err
        :val (Throwable->str ex)
        :form (:source read-result)}))

   :repl-result
   (fn [_ ret]
     (out-fn ret))

   :repl-stderr
   (fn [{:keys [ns read-result]} text]
     (send-over-backchannel
       {:tag :err
        :ns (str ns)
        :val (str text "\n")
        :form (:source read-result)}))

   :repl-stdout
   (fn [_ text]
     (send-over-backchannel
       {:tag :out :val text}))})

(defn repl
  ([]
   (repl {}))
  ([{:keys [build-id] :as opts}]
   (let [lock (Object.)
         close-signal (async/promise-chan)
         out-fn #(binding [*flush-on-newline* true]
                   (locking lock
                     (pprint/pprint
                       (binding [*default-data-reader-fn* tagged-literal
                                 *read-eval* false]
                         (some-> % read-string)))))
         {backchannel :socket
          send-over-backchannel :send-over-backchannel}
         (backchannel/open
           (assoc opts
             :xform-in #(assoc % :build-id build-id :in *in*)
             :xform-out #(dissoc % :in)))]
     (try
       (let [_ (prn {:greeting (let [{:keys [major minor qualifier]} *clojurescript-version*]
                                 (format "ClojureScript %s.%s.%s\n" major minor qualifier))
                     :host (-> backchannel .getInetAddress .getHostName)
                     :port (-> backchannel .getLocalPort)})
             {:keys [supervisor relay clj-runtime]} (api/get-runtime!)
             worker (supervisor/get-worker supervisor build-id)
             spec (spec-for-runtime out-fn send-over-backchannel (:client-id clj-runtime))]
         (repl-impl/do-repl worker relay *in* close-signal spec))
       (catch ExceptionInfo ex
         (send-over-backchannel {:tag :err :val (Throwable->str ex)}))
       (catch AssertionError ex
         (send-over-backchannel {:tag :err :val (Throwable->str ex)}))
       (finally
         (async/>!! close-signal true)
         (.close backchannel))))))
