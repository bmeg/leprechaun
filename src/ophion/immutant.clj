(ns ophion.immutant
  (:require
   [cheshire.core :as json]
   [clojure.java.io :as io]
   [polaris.core :as polaris]
   [taoensso.timbre :as log]
   [ring.middleware.resource :as ring]
   [immutant.web :as web]
   ;; [immutant.web.async :as async]
   [protograph.kafka :as kafka]
   [ophion.config :as config]
   [ophion.db :as db]
   [ophion.query :as query]
   [ophion.search :as search])
  (:import
   [java.io InputStreamReader]
   [ch.qos.logback.classic Logger Level]))

(.setLevel
 (org.slf4j.LoggerFactory/getLogger
  (Logger/ROOT_LOGGER_NAME))
 Level/INFO)

(defn append-newline
  [s]
  (str s "\n"))

(def output
  (comp
   append-newline
   json/generate-string
   query/translate))

(defn default-graph
  []
  (let [graph (db/connect-graph "config/ophion.clj")
        search (search/connect {:index "test"})]
    {:graph graph
     :search search}))

(defn schema
  [request]
  {:status 200
   :headers {"content-type" "application/json"}
   :body (config/resource "config/bmeg.protograph.json")})

(defn find-vertex-handler
  [graph request]
  (let [gid (-> request :params :gid)
        vertex (query/find-vertex graph gid)
        out (query/vertex-connections vertex)]
    {:status 200
     :headers {"content-type" "application/json"}
     :body (json/generate-string out)}))

(defn vertex-query-handler
  [graph search request]
  (let [raw-query (json/parse-stream (InputStreamReader. (:body request)) keyword)
        query (query/delabelize raw-query)
        _ (log/info (mapv identity query))
        result (query/evaluate {:graph graph :search search} query)
        out (map output result)]
    (db/commit graph)
    {:status 200
     :headers {"content-type" "application/json"}
     :body out}))

;; (defn vertex-query-handler
;;   [graph search request]
;;   (let [raw-query (json/parse-stream (InputStreamReader. (:body request)) keyword)
;;         query (query/delabelize raw-query)
;;         _ (log/info (mapv identity query))
;;         result (query/evaluate {:graph graph :search search} query)
;;         out (map output result)
;;         source (stream/->source out)]
;;     (stream/on-drained
;;      source
;;      (fn []
;;        (log/debug "query complete")
;;        (db/commit graph)))
;;     {:status 200
;;      :headers {"content-type" "application/json"}
;;      :body source}))

(defn find-edge-handler
  [graph request]
  {:status 200
   :headers {"content-type" "application/json"}
   :body "found"})

(defn edge-query-handler
  [graph request]
  {:status 200
   :headers {"content-type" "application/json"}
   :body "found"})

(defn find-vertex
  [graph]
  (fn [request]
    (#'find-vertex-handler graph request)))

(defn vertex-query
  [graph search]
  (fn [request]
    (#'vertex-query-handler graph search request)))

(defn find-edge
  [graph]
  (fn [request]
    (#'find-edge-handler graph request)))

(defn edge-query
  [graph]
  (fn [request]
    (#'edge-query-handler graph request)))

(defn home
  [request]
  {:status 200
   :headers {"content-type" "text/html"}
   :body (config/resource "public/viewer.html")})

(defn ophion-routes
  [graph search]
  [["/" :home #'home]
   ["/schema/protograph" :schema #'schema]
   ["/vertex/find/:gid" :vertex-find (find-vertex graph)]
   ["/vertex/query" :vertex-query (vertex-query graph search)]
   ["/edge/find/:out/:label/:in" :edge-find (find-edge graph)]
   ["/edge/query" :edge-query (edge-query graph)]])

(defn start
  []
  (log/info "starting server")
  (let [config (config/read-config "config/ophion.clj")
        graph (db/connect (:graph config))
        search (search/connect (:search config))
        routes (polaris/build-routes (ophion-routes graph search))
        router (ring/wrap-resource (polaris/router routes) "public")]
    (web/run
      #'home ;; (polaris/router routes) ;; router
      :port (or (:port config) 4443))))

;; (defn ophion-static
;;   [request]
;;   {:status 200
;;    :body "ophion"})

;; (def graph (query/tinkergraph))

;; (defn ophion
;;   [request]
;;   (info (str request))
;;   (async/as-channel
;;    request
;;    {:on-open
;;     (fn [stream]
;;       (let [reader (InputStreamReader. (:body request))
;;             query (json/read reader :key-fn keyword)
;;             result (query/evaluate graph query)]
;;         (map
;;          (comp async/send! query/translate)
;;          (iterator-seq result))))}))

;; (defn start
;;   []
;;   (info "starting server")
;;   (web/run #'ophion {:port 4443}))

(defn -main
  []
  (start))
