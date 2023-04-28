(ns tutkain.deps
  (:require
   [clojure.edn :as edn]
   [clojure.java.io :as io]
   [clojure.repl.deps :as deps]
   [clojure.xml :as xml]
   [tutkain.rpc :refer [handle respond-to]])
  (:import (java.io PushbackReader)
           (java.net URI URLEncoder)
           (java.net.http HttpClient HttpClient$Redirect HttpRequest HttpResponse$BodyHandlers)
           (java.util.zip GZIPInputStream)))

(defmethod handle :sync-deps
  [message]
  (try
    (deps/sync-deps (select-keys message [:aliases]))
    (respond-to message {:tag :ret :val :ok})
    (catch Exception ex
      (respond-to message {:tag :err :val (.getMessage ex)}))))

(defmethod handle :add-lib
  [{:keys [lib] :as message}]
  (try
    (deps/add-lib lib)
    (respond-to message {:tag :ret :val :ok})
    (catch Exception ex
      (respond-to message {:tag :err :val (.getMessage ex)}))))

(defmethod handle :add-libs
  [{:keys [lib-coords] :as message}]
  (try
    (deps/add-libs lib-coords)
    (respond-to message {:tag :ret :val :ok})
    (catch Exception ex
      (respond-to message {:tag :err :val (.getMessage ex)}))))

(defn ^:private http-request
  [uri]
  (let [http-client (.. (HttpClient/newBuilder) (followRedirects HttpClient$Redirect/NORMAL) (build))
        body-handler (HttpResponse$BodyHandlers/ofInputStream)
        request-builder (HttpRequest/newBuilder)
        request (.. request-builder (uri uri) (build))
        response (.send http-client request body-handler)]
    (.body response)))

(defmethod handle :find-libs
  [{:keys [repo q max-results]
    :or {max-results 25}
    :as message}]
  (try
    (case repo
      clojars
      (let [uri (URI/create (format "https://clojars.org/search?q=%s&format=xml" (URLEncoder/encode q)))
            response (http-request uri)
            results (into []
                      (comp
                        (take max-results)
                        (map :attrs)
                        (map (fn [{:keys [description group_name jar_name version]}]
                               {:group-id group_name
                                :artifact-id jar_name
                                :version {:mvn/version version}
                                :description description})))
                      (some-> response xml/parse :content))]
        (respond-to message {:results results}))

      maven
      (let [uri (URI/create (format "https://search.maven.org/solrsearch/select?q=%s&rows=%d&wt=xml" (URLEncoder/encode q) max-results))
            response (http-request uri)
            results (into []
                      (comp
                        (take max-results)
                        (map :content)
                        (map (fn [doc]
                               (let [group-id (-> doc (nth 2) :content first)
                                     artifact-id (-> doc (nth 0) :content first)
                                     version (-> doc (nth 4) :content first)]
                                 {:group-id group-id
                                  :artifact-id artifact-id
                                  :version {:mvn/version version}}))))
                      (some-> response xml/parse :content second :content))]
        (respond-to message {:results results}))

      github
      (let [uri (URI/create "https://github.com/phronmophobic/dewey/releases/latest/download/deps-libs.edn.gz")
            response (http-request uri)
            results (with-open [reader (-> response GZIPInputStream. io/reader PushbackReader.)]
                      (into []
                        (comp
                          (map (fn [[_ {:keys [description lib url versions]}]]
                                 {:group-id (some-> lib namespace)
                                  :artifact-id (name lib)
                                  :url url
                                  :version (first versions)
                                  :description description}))
                          (filter :version))
                        (sort-by key (edn/read reader))))]
        (respond-to message {:results results})))
    (catch Exception ex
      (respond-to message {:tag :err :val (or (.getMessage ex) "Unknown error")}))))
