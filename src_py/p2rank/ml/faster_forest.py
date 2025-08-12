"""
Pure-Python evaluator for P2Rank FasterForest (flattened) models.

Loads arrays exported from Java (child indices, feature indices, thresholds, leaf scores)
and performs per-sample predictions identical to Java's FasterForest flattened inference by
traversing each tree and combining leaf statistics.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

import numpy as np


@dataclass
class FlatForestArrays:
    child_left: np.ndarray  # shape (n_nodes,), int
    child_right: np.ndarray  # shape (n_nodes,), int
    feature_index: np.ndarray  # shape (n_nodes,), int
    threshold: np.ndarray  # shape (n_nodes,), float
    node_prob: np.ndarray  # shape (n_leaves,), float
    left_leaf_id: np.ndarray  # shape (n_nodes,), int (-1 if not leaf)
    right_leaf_id: np.ndarray  # shape (n_nodes,), int (-1 if not leaf)
    num_trees: int
    num_attributes: int
    roots: np.ndarray  # shape (num_trees,), int
    leaf_class0: np.ndarray | None = None
    leaf_class1: np.ndarray | None = None


class FlatBinaryForestPy:
    def __init__(self, arrays: FlatForestArrays):
        self.arr = arrays

        n = self.arr.child_left.shape[0]
        assert (
            self.arr.child_right.shape[0]
            == self.arr.feature_index.shape[0]
            == self.arr.threshold.shape[0]
            == n
        ), "All node arrays must have the same length"
        assert len(self.arr.roots) == self.arr.num_trees, "roots size must match num_trees"

        self.arr.child_left = self.arr.child_left.astype(np.int64, copy=False)
        self.arr.child_right = self.arr.child_right.astype(np.int64, copy=False)
        self.arr.feature_index = self.arr.feature_index.astype(np.int64, copy=False)
        self.arr.threshold = self.arr.threshold.astype(np.float64, copy=False)
        self.arr.node_prob = self.arr.node_prob.astype(np.float64, copy=False)
        self.arr.left_leaf_id = self.arr.left_leaf_id.astype(np.int64, copy=False)
        self.arr.right_leaf_id = self.arr.right_leaf_id.astype(np.int64, copy=False)
        self.arr.roots = self.arr.roots.astype(np.int64, copy=False)
        if self.arr.leaf_class0 is not None:
            self.arr.leaf_class0 = self.arr.leaf_class0.astype(np.float64, copy=False)
        if self.arr.leaf_class1 is not None:
            self.arr.leaf_class1 = self.arr.leaf_class1.astype(np.float64, copy=False)

    @staticmethod
    def load_npz(npz_path: Path) -> "FlatBinaryForestPy":
        data = np.load(npz_path)
        roots = data.get("roots")
        if roots is None:
            n = int(data["child_left"].shape[0])
            all_idx = np.arange(n, dtype=np.int64)
            children = []
            for name in ("child_left", "child_right"):
                arr = data[name].astype(np.int64, copy=False)
                children.append(arr[arr >= 0])
            child_set = np.unique(np.concatenate(children)) if children else np.array([], dtype=np.int64)
            roots = np.setdiff1d(all_idx, child_set, assume_unique=False)
        arrays = FlatForestArrays(
            child_left=data["child_left"],
            child_right=data["child_right"],
            feature_index=data["feature_index"],
            threshold=data["threshold"],
            node_prob=data["node_prob"],
            left_leaf_id=data["left_leaf_id"],
            right_leaf_id=data["right_leaf_id"],
            num_trees=int(data["num_trees"]),
            num_attributes=int(data["num_attributes"]),
            roots=roots,
            leaf_class0=data.get("leaf_class0"),
            leaf_class1=data.get("leaf_class1"),
        )
        return FlatBinaryForestPy(arrays)

    def _predict_one(self, x: np.ndarray) -> float:
        arr = self.arr
        if arr.leaf_class0 is not None and arr.leaf_class1 is not None:
            sum_c0 = 0.0
            sum_c1 = 0.0
            for root in arr.roots:
                i = int(root)
                while True:
                    feat = arr.feature_index[i]
                    thr = arr.threshold[i]
                    go_left = x[feat] < thr  # strict less-than per Java bytecode
                    if go_left and arr.left_leaf_id[i] >= 0:
                        lid = arr.left_leaf_id[i]
                        sum_c0 += arr.leaf_class0[lid]
                        sum_c1 += arr.leaf_class1[lid]
                        break
                    if (not go_left) and arr.right_leaf_id[i] >= 0:
                        lid = arr.right_leaf_id[i]
                        sum_c0 += arr.leaf_class0[lid]
                        sum_c1 += arr.leaf_class1[lid]
                        break
                    i = int(arr.child_left[i]) if go_left else int(arr.child_right[i])
            denom = sum_c0 + sum_c1
            return (sum_c1 / denom) if denom > 0.0 else 0.0
        else:
            # fallback: average per-tree positive probability
            total = 0.0
            for root in arr.roots:
                i = int(root)
                while True:
                    feat = arr.feature_index[i]
                    thr = arr.threshold[i]
                    go_left = x[feat] < thr
                    if go_left and arr.left_leaf_id[i] >= 0:
                        total += arr.node_prob[arr.left_leaf_id[i]]
                        break
                    if (not go_left) and arr.right_leaf_id[i] >= 0:
                        total += arr.node_prob[arr.right_leaf_id[i]]
                        break
                    i = int(arr.child_left[i]) if go_left else int(arr.child_right[i])
            return total / float(arr.num_trees)

    def predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        return np.array([self._predict_one(row) for row in X], dtype=np.float64)


