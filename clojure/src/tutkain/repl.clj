(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint]
   [tutkain.backchannel :as backchannel]
   [tutkain.format :as format])
  (:import
   (java.io File)
   (java.util Date)))

(def ^:dynamic ^:experimental *print*
  "A function you can use as the :print arg of clojure.main/repl."
  prn)

(def ^:dynamic ^:experimental *caught*
  "A function you can use as the :caught arg of clojure.main/repl."
  main/repl-caught)

(defonce ^{:doc "An atom containing your REPL evaluation history. Persists across connections."} history
  (atom []))

(defn ^:private add-history-entry
  [max-history entry]
  (swap! history
    (fn [h v]
      (if (>= (count h) max-history)
        (conj (subvec h 1) v)
        (conj h v)))
    (assoc entry :inst (Date.))))

(defn reval
  []
  (let [form (-> @history peek :form)]
    (when (not= form '(tutkain.repl/reval))
      (eval form))))

(defn repl
  "Tutkain's main read-eval-print loop.

  Like clojure.core.server/io-prepl, with these differences:

  - Starts a backchannel socket server that Tutkain uses for editor tooling
    (auto-completion, metadata lookup, etc.)
  - Pretty-prints evaluation results and exception maps
  - Binds *print* and *caught* for use with nested REPLs started via
    clojure.main/repl
  - Binds *file* and *source-path* to vals sent via backchannel when evaluating
    to ensure useful exception stack traces"
  ([]
   (repl {}))
  ([{:keys [max-history] :or {max-history 100} :as opts}]
   (let [EOF (Object.)
         lock (Object.)
         out *out*
         in *in*
         out-fn (fn [message]
                  (binding [*print-readably* true
                            pprint/*print-right-margin* 100]
                    (locking lock
                      (pprint/pprint message out)
                      (.flush out))))
         repl-thread (Thread/currentThread)]
     (main/with-bindings
       (in-ns 'user)
       (apply require main/repl-requires)
       (let [{backchannel :socket
              send-over-backchannel :send-over-backchannel}
             (backchannel/open
               (assoc opts
                 :xform-in #(assoc % :in in :repl-thread repl-thread)
                 :xform-out #(dissoc % :in)))]
         (try
           (out-fn {:greeting (str "Clojure " (clojure-version) "\n")
                    :host (-> backchannel .getInetAddress .getHostName)
                    :port (-> backchannel .getLocalPort)})
           (loop []
             (when
               (try
                 (let [[form s] (read+string {:eof EOF :read-cond :allow} in)
                       file (:file @backchannel/eval-context)]
                   (binding [*file* (or file "NO_SOURCE_PATH")
                             *source-path* (or (some-> file File. .getName) "NO_SOURCE_FILE")]
                     (try
                       (when-not (identical? form EOF)
                         (if (and (list? form) (= 'tutkain/eval (first form)))
                           (do
                             (apply eval (rest form))
                             true)
                           (let [ret (eval form)]
                             (when-not (= :repl/quit ret)
                               (set! *3 *2)
                               (set! *2 *1)
                               (set! *1 ret)
                               (out-fn ret)
                               (future (add-history-entry max-history {:inst (Date.) :form form :ret ret}))
                               true))))
                       (catch Throwable ex
                         (set! *e ex)
                         (reset! backchannel/most-recent-exception ex)
                         (send-over-backchannel {:tag :err
                                                 :val (format/Throwable->str ex)
                                                 :ns (str (.name *ns*))
                                                 :form s})
                         true))))
                 (catch Throwable ex
                   (set! *e ex)
                   (reset! backchannel/most-recent-exception ex)
                   (send-over-backchannel
                     {:tag :ret
                      :val (format/pp-str (assoc (Throwable->map ex) :phase :read-source))
                      :ns (str (.name *ns*))
                      :exception true})
                   true))
               (recur)))
           (finally
             (.close backchannel))))))))
