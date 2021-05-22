(ns tutkain.socket
  (:import
   (java.io BufferedReader InputStreamReader PrintWriter)
   (java.net Socket)
   (java.util.concurrent LinkedBlockingQueue)))

(defn client
  [& {:keys [host port recvq]}]
  (let [socket (Socket. host port)
        output (.getOutputStream socket)
        writer (PrintWriter. output true)
        input (.getInputStream socket)
        reader (-> input InputStreamReader. BufferedReader.)
        q (LinkedBlockingQueue.)]
    (future
      (loop []
        (when-not (.isClosed socket)
          (when-some [result (.readLine reader)]
            (.put recvq result)
            (recur)))))

    (future
      (loop []
        (let [item (.take q)]
          (when-not (= ::quit item)
            (.println writer (pr-str item))
            (recur))))
      (.shutdownInput socket))
    q))

(comment
  (def recvq (LinkedBlockingQueue.))
  (def sendq (client :host "localhost" :port 1235 :recvq recvq))
  (.put sendq "Hello")
  (.take recvq)
  (.put sendq ::quit)
  )
