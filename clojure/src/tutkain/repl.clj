(ns tutkain.repl
  (:require
   [clojure.main :as main]
   [clojure.pprint :as pprint]
   [tutkain.backchannel :as backchannel]
   [tutkain.format :as format])
  (:import
   (java.io Writer)
   (java.util.concurrent Executors TimeUnit)))

(def ^:dynamic ^:experimental *print*
  "A function you can use as the :print arg of clojure.main/repl."
  prn)

(def ^:dynamic ^:experimental *caught*
  "A function you can use as the :caught arg of clojure.main/repl."
  main/repl-caught)

(defn ^:private read-in-context
  "Given an eval context and a LineNumberingPushbackReader, read a form from
  the reader in the context of the eval context thread bindings and return
  the eval context with these keys added:

  - :form - The object read
  - :string - The string read"
  [eval-context ^clojure.lang.LineNumberingPushbackReader reader]
  (.unread reader (.read reader))
  (let [eval-context @eval-context
        [form string] (with-bindings (:thread-bindings eval-context {})
                        (read+string {:eof ::EOF :read-cond :allow} reader))]
    (assoc eval-context :form form :string string)))

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
  "Tutkain's main read-eval-print loop.

  - Starts a backchannel socket server that Tutkain uses for editor tooling
    (auto-completion, metadata lookup, etc.)
  - Pretty-prints evaluation results and exception maps
  - Binds *print* for use with nested REPLs started via
    clojure.main/repl"
  ([]
   (repl {}))
  ([opts]
   (let [lock (Object.)
         out *out*
         in *in*
         pretty-print (fn [message]
                        (binding [*print-readably* true
                                  pprint/*print-right-margin* 100]
                          (locking lock
                            (pprint/pprint message out))))
         repl-thread (Thread/currentThread)
         debounce-service (Executors/newScheduledThreadPool 1)
         debounce (make-debouncer debounce-service)]
     (main/with-bindings
       (in-ns 'user)
       (apply require main/repl-requires)
       (let [{backchannel :socket
              eval-context :eval-context
              send-over-backchannel :send-over-backchannel}
             (backchannel/open
               (assoc opts
                 :xform-in #(assoc % :in in :repl-thread repl-thread)
                 :xform-out #(dissoc % :in)))
             ;; Prevent stdout/stderr from interleaving with eval results by
             ;; binding *out* and *err* such that they write into auxiliary
             ;; PrintWriters that send strings to client via backchannel, then
             ;; debounce flush said auxiliary PrintWriters.
             out-writer (PrintWriter-on #(send-over-backchannel {:tag :out :val %1}) nil)
             err-writer (PrintWriter-on #(send-over-backchannel {:tag :err :val %1}) nil)
             flush-out (debounce #(.flush out-writer) 10)
             flush-err (debounce #(.flush err-writer) 10)
             write-out (fn [string] (.write out-writer string) (flush-out))
             write-err (fn [string] (.write err-writer string) (flush-err))]
         (binding [*out* (PrintWriter-on write-out #(.close out-writer))
                   *err* (PrintWriter-on write-err #(.close err-writer))
                   *print* pretty-print]
           (try
             (pretty-print {:greeting (str "Clojure " (clojure-version) "\n")
                            :host (-> backchannel .getInetAddress .getHostName)
                            :port (-> backchannel .getLocalPort)})
             (loop []
               (when
                 (try
                   (let [{:keys [thread-bindings response form string]} (read-in-context eval-context in)
                         ;; For (read-line) support. See also:
                         ;;
                         ;; https://clojure.atlassian.net/browse/CLJ-2692
                         _ (main/skip-whitespace in)
                         backchannel-response? (#{:inline :clipboard} (:output response))]
                     (with-bindings thread-bindings
                       (when-not (identical? form ::EOF)
                         (try
                           (let [ret (eval form)]
                             (.flush ^Writer *out*)
                             (.flush ^Writer *err*)
                             (when-not (= :repl/quit ret)
                               (set! *3 *2)
                               (set! *2 *1)
                               (set! *1 ret)
                               (if backchannel-response?
                                 (send-over-backchannel
                                   (assoc response :tag :ret :val (format/pp-str ret)))
                                 (pretty-print ret))
                               (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                               true))
                           (catch Throwable ex
                             (.flush ^Writer *out*)
                             (.flush ^Writer *err*)
                             (set! *e ex)
                             (send-over-backchannel
                               (merge response {:tag :err
                                                :val (format/Throwable->str ex)
                                                :ns (str (.name *ns*))
                                                :form string}))
                             (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                             true)))))
                   (catch Throwable ex
                     (set! *e ex)
                     (send-over-backchannel
                       {:tag :ret
                        :val (format/pp-str (assoc (Throwable->map ex) :phase :read-source))
                        :ns (str (.name *ns*))
                        :exception true})
                     (swap! eval-context assoc :thread-bindings (get-thread-bindings))
                     true))
                 (recur)))
             (finally
               (.shutdown debounce-service)
               (.close backchannel)))))))))
