(ns tutkain.repl.runtime.test
  (:require
   [clojure.stacktrace :as stacktrace]
   [clojure.string :as str]
   [clojure.test :as test]
   [clojure.walk :as walk]
   [tutkain.repl.runtime.repl :refer [handle pp-str response-for]])
  (:import
   (clojure.lang LineNumberingPushbackReader)
   (java.io File StringReader)))

(defn organize
  [x]
  (walk/postwalk
    #(cond
       (map? %) (into (sorted-map) %)
       :else %)
    x))

(defn- pprint-expected
  [{:keys [actual expected] :as event}]
  (if (and (= (first expected) '=) (sequential? actual))
    (assoc event :expected (->> actual last second organize pp-str))
    (update event :expected str)))

(defn- pprint-actual
  [{:keys [actual] :as event}]
  (if (sequential? actual)
    (update event :actual (comp pp-str organize last last))
    (update event :actual pp-str)))

(defn- event-var-meta
  [event]
  (-> event :var meta (select-keys [:line :column :file :name :ns]) (update :ns str)))

(defn- class-name-prefix
  [ns]
  (str/replace (format "%s$" ns) "-" "_"))

(defn- line-number
  [ns]
  (->>
    (.getStackTrace (new java.lang.Throwable))
    (drop-while #(not (str/starts-with? (.getClassName ^StackTraceElement %)
                        (class-name-prefix ns))))
    (first)
    (.getLineNumber)))

(defn- add-result
  [results id result]
  (swap! results update id (fnil conj []) result))

(defn ^:private clean-ns!
  [ns]
  (some->> ns ns-aliases (run! #(ns-unalias ns (first %))))
  (some->> ns ns-publics
    (filter (fn [[_ v]] (-> v meta :test)))
    (run! (fn [[sym _]] (ns-unmap ns sym)))))

(defmethod handle :test
  [{:keys [ns code file vars out-fn] :as message}]
  (let [ns-sym (or (some-> ns symbol) 'user)]
    (try
      (clean-ns! (find-ns ns-sym))
      (Compiler/load (LineNumberingPushbackReader. (StringReader. code)) file (-> file File. .getName))
      (let [results (atom {:fail [] :pass [] :error []})
            var-meta (atom nil)]
        (binding [test/report (fn [event*]
                                (let [{:keys [type] :as event} (cond-> event* (seq file) (assoc :file file))]
                                  ;; TODO: Could use a multimethod here instead.
                                  (case type
                                    :begin-test-var (reset! var-meta (event-var-meta event))
                                    :end-test-var (reset! var-meta nil)
                                    :fail (do
                                            (test/inc-report-counter :assert)
                                            (test/inc-report-counter :fail)
                                            (add-result results :fail
                                              (-> event
                                                pprint-expected
                                                pprint-actual
                                                (assoc :var-meta @var-meta))))
                                    :pass (do
                                            (test/inc-report-counter :assert)
                                            (test/inc-report-counter :pass)
                                            (add-result results :pass
                                              {:type :pass :line (line-number ns-sym) :var-meta @var-meta}))
                                    :error (do
                                             (test/inc-report-counter :assert)
                                             (test/inc-report-counter :error)
                                             (add-result results :error
                                               (-> event
                                                 pprint-expected
                                                 (update :actual #(with-out-str (stacktrace/print-stack-trace %)))
                                                 (assoc :var-meta @var-meta))))
                                    :summary (swap! results assoc :summary (-> event (dissoc :file) str))
                                    nil)))]
          (if (seq vars)
            (binding [test/*report-counters* (ref test/*initial-report-counters*)]
              (test/test-vars (map #(resolve (symbol ns %)) vars))
              (swap! results assoc :summary (str (assoc @test/*report-counters* :type :summary))))
            (test/run-tests ns-sym)))
        (out-fn (response-for message @results)))
      (catch Throwable ex
        (out-fn (response-for message {:tag :ret
                                       :ns (str (.name *ns*))
                                       :val (pp-str (assoc (Throwable->map ex) :phase :execution))
                                       :exception true}))))))
