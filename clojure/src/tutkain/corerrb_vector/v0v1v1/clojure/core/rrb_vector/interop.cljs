(ns tutkain.corerrb-vector.v0v1v1.clojure.core.rrb-vector.interop
  (:require [tutkain.corerrb-vector.v0v1v1.clojure.core.rrb-vector.protocols
             :refer [PSliceableVector -slicev
                     PSpliceableVector -splicev]]
            [tutkain.corerrb-vector.v0v1v1.clojure.core.rrb-vector.rrbt :refer [-as-rrbt]]))

(extend-protocol PSliceableVector
  cljs.core/PersistentVector
  (-slicev [v start end]
    (-slicev (-as-rrbt v) start end))

  cljs.core/Subvec
  (-slicev [v start end]
    (-slicev (-as-rrbt v) start end)))

(extend-protocol PSpliceableVector
  cljs.core/PersistentVector
  (-splicev [v1 v2]
    (-splicev (-as-rrbt v1) v2))

  cljs.core/Subvec
  (-splicev [v1 v2]
    (-splicev (-as-rrbt v1) v2)))
