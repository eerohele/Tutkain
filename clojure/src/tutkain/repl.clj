(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint]
   [tutkain.backchannel :as backchannel]
   [tutkain.format :as format]))

(def ^:dynamic ^:experimental *print*
  "A function you can use as the :print arg of clojure.main/repl."
  prn)

(def ^:dynamic ^:experimental *caught*
  "A function you can use as the :caught arg of clojure.main/repl."
  main/repl-caught)

(defmacro switch-ns
  [namespace]
  `(or (some->> '~namespace find-ns ns-name in-ns .name) (ns ~namespace)))

(defn repl
  "Tutkain's main read-eval-print loop.

  - Starts a backchannel socket server that Tutkain uses for editor tooling
    (auto-completion, metadata lookup, etc.)
  - Pretty-prints evaluation results and exception maps
  - Binds *print* for use with nested REPLs started via
    clojure.main/repl"
  ([]
   (repl {}))
  ([opts]
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
                 :xform-out #(dissoc % :in)))
             prompt+input (fn [ns s]
                            (send-over-backchannel {:tag :out :val (format "%s=> " (ns-name ns))})
                            (send-over-backchannel {:tag :ret :val (str s \newline)}))]
         (binding [*out* (PrintWriter-on #(send-over-backchannel {:tag :out :val %1}) nil)
                   *err* (PrintWriter-on #(send-over-backchannel {:tag :err :val %1}) nil)
                   *print* out-fn]
           (try
             (out-fn {:greeting (str "Clojure " (clojure-version) "\n")
                      :host (-> backchannel .getInetAddress .getHostName)
                      :port (-> backchannel .getLocalPort)})
             (loop []
               (when
                 (try
                   (let [[form s] (read+string {:eof EOF :read-cond :allow} in)
                         silent? (and (list? form) (= 'tutkain.repl/switch-ns (first form)))]
                     (with-bindings @backchannel/eval-context
                       (when-not (identical? form EOF)
                         (when-not silent?
                           (prompt+input *ns* s))
                         (try
                           (if silent?
                             (do (eval form) true)
                             (let [ret (eval form)]
                               (when-not (= :repl/quit ret)
                                 (set! *3 *2)
                                 (set! *2 *1)
                                 (set! *1 ret)
                                 (backchannel/reset-eval-context! (get-thread-bindings))
                                 (out-fn ret)
                                 true)))
                           (catch Throwable ex
                             (set! *e ex)
                             (backchannel/reset-eval-context! (get-thread-bindings))
                             (send-over-backchannel {:tag :err
                                                     :val (format/Throwable->str ex)
                                                     :ns (str (.name *ns*))
                                                     :form s})
                             true)))))
                   (catch Throwable ex
                     (set! *e ex)
                     (backchannel/reset-eval-context! (get-thread-bindings))
                     (send-over-backchannel
                       {:tag :ret
                        :val (format/pp-str (assoc (Throwable->map ex) :phase :read-source))
                        :ns (str (.name *ns*))
                        :exception true})
                     true))
                 (recur)))
             (finally
               (.close backchannel)))))))))
