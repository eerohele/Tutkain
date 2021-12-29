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
         plain-print #(binding [*out* out] (println %))
         pretty-print (fn [message]
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
              eval-context :eval-context
              send-over-backchannel :send-over-backchannel}
             (backchannel/open
               (assoc opts
                 :xform-in #(assoc % :in in :repl-thread repl-thread)
                 :xform-out #(dissoc % :in)))]
         (binding [*out* (PrintWriter-on #(send-over-backchannel {:tag :out :val %1}) nil)
                   *err* (PrintWriter-on #(send-over-backchannel {:tag :err :val %1}) nil)
                   *print* pretty-print]
           (try
             (pretty-print {:greeting (str "Clojure " (clojure-version) "\n")
                            :host (-> backchannel .getInetAddress .getHostName)
                            :port (-> backchannel .getLocalPort)})
             (loop []
               (when
                 (try
                   (let [[form s] (read+string {:eof EOF :read-cond :allow} in)
                         {:keys [thread-bindings response]} @eval-context
                         backchannel-response? (#{:inline :clipboard} (:output response))]
                     (with-bindings thread-bindings
                       (when-not (identical? form EOF)
                         (try
                           (if (and (list? form) (= 'tutkain.repl/switch-ns (first form)))
                             (do (eval form) true)
                             (do
                               (when-not backchannel-response?
                                 (plain-print (format "%s=> %s" (ns-name *ns*) s)))
                               (let [ret (eval form)]
                                 (when-not (= :repl/quit ret)
                                   (set! *3 *2)
                                   (set! *2 *1)
                                   (set! *1 ret)
                                   (swap! eval-context assoc #'*3 *3 #'*2 *2 #'*1 *1)
                                   (if backchannel-response?
                                     (send-over-backchannel
                                       (assoc response :tag :ret :val (format/pp-str ret)))
                                     (pretty-print ret))
                                   (flush)
                                   true))))
                           (catch Throwable ex
                             (set! *e ex)
                             (swap! eval-context assoc #'*e *e)
                             (send-over-backchannel
                               {:tag :err
                                :val (format/Throwable->str ex)
                                :ns (str (.name *ns*))
                                :form s})
                             (flush)
                             true)))))
                   (catch Throwable ex
                     (set! *e ex)
                     (swap! eval-context assoc #'*e *e)
                     (send-over-backchannel
                       {:tag :ret
                        :val (format/pp-str (assoc (Throwable->map ex) :phase :read-source))
                        :ns (str (.name *ns*))
                        :exception true})
                     true))
                 (recur)))
             (finally
               (.close backchannel)))))))))
