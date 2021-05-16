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
        reader (BufferedReader. (InputStreamReader. input))
        q (LinkedBlockingQueue.)]
    (future
      (loop []
        (let [item (.take q)]
          (when-not (= ::quit item)
            (.println writer (pr-str item))
            (recur))))

      (.shutdownOutput socket))

    (future
      (loop []
        (when-some [result (.readLine reader)]
          (.put recvq result)
          (recur))))
    q))
