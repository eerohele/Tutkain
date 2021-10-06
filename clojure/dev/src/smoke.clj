;; lookup over backchannel

(map inc (range 10))

;; completions over backchannel

;; keywords
:a

;; symbols
map

;; host language things
clojure.lang.
java.

;; interrupts over backchannel (ugly exception though)

(Thread/sleep Integer/MAX_VALUE)
(println "Hello, world!")

;; still a streaming REPL (message frames don't interfere with reading)
(defn bmi
  [mass height]
  (->
    (/ (* mass 1.3) (Math/pow (/ height 100) 2.5))
    bigdec
    (.setScale 0 BigDecimal/ROUND_HALF_UP)))

(comment
  (bmi 60 170)
  )

(defn prompt-bmi
  []
  (let [_ (println "How much do you weigh in kilograms?")
        mass (read)
        _ (println (format "%s kilos, all right. How tall are you in centimeters?" mass))
        height (read)
        _ (println (format "So that's %skg and %scm, gotcha." mass height))]
    (format "That means your body mass index is %s." (bmi mass height))))

(comment
  (prompt-bmi)
  62
  170
  )

;; tap
(tap> 1)

(require '[clojure.main :as main])

(defn contextual-eval
  [ctx expr]
  (eval
    `(let [~@(mapcat (fn [[k v]] [k `'~v]) ctx)]
       ~expr)))

(defmacro local-context
  []
  (let [symbols (keys &env)]
    (zipmap (map (fn [sym] `(quote ~sym)) symbols) symbols)))

(defn readr
  [prompt exit-code]
  (let [input (main/repl-read prompt exit-code)]
    (if (= input ::tl)
      exit-code
      input)))

(defmacro break []
  `(clojure.main/repl
     :init #(print "<<<DEBUG>>>")
     :need-prompt (constantly false)
     :prompt (constantly "")
     :read readr
     :eval (partial contextual-eval (local-context))))

(defn div
  [n d]
  (break)
  (int (/ n d)))

(div 10 0)
::tl

;; https://www.cognitect.com/blog/2017/6/5/repl-debugging-no-stacktrace-required
(defn foo
  [n]
  (cond
    (> n 40) (+ n 20)
    (> n 20) (- (first n) 20)
    :else 0))
