(ns tutkain.shadow
  (:require
   [clojure.core.async :as async]
   [shadow.cljs.devtools.api :as api]
   [shadow.cljs.devtools.server.repl-impl :as repl-impl]
   [shadow.cljs.devtools.server.supervisor :as supervisor]
   [tutkain.format :refer [pp-str Throwable->str]]
   [tutkain.backchannel :as backchannel])
  (:import
   (clojure.lang ExceptionInfo)))

(defn pp-ret
  "Pretty-print a ClojureScript evaluation result.

  ClojureScript evaluation results are strings. That means we must first try
  to read them. If the Clojure reader can't read the result, we fall back to
  the original result followed by a newline."
  [ret]
  (try
    (binding [*default-data-reader-fn* tagged-literal
              *read-eval* false]
      (-> ret read-string pp-str))
    (catch Throwable _
      (str ret \newline))))

(comment
  (pp-ret "{:a 1}")
  (pp-ret "#object [Function]")
  (pp-ret "#object [foo.bar.Baz]")
  (pp-ret "#object [object Window]")
  (pp-ret "#js {:foo 1 :bar 2}")
  (pp-ret "#queue [1 2 3]")
  (pp-ret ":::1")
  )

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
        :val (pp-ret ret)}))

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
