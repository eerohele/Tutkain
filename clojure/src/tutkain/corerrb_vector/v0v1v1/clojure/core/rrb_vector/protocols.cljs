(ns tutkain.corerrb-vector.v0v1v1.clojure.core.rrb-vector.protocols)

(defprotocol PSpliceableVector
  (-splicev [v1 v2]))

(defprotocol PSliceableVector
  (-slicev [v start end]))
