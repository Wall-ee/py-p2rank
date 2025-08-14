#!/usr/bin/env python3
"""
Baseline training script (non-equivalence line)

Train simple classifiers on P2Rank-style feature matrices using:
- scikit-learn RandomForestClassifier (default)
- optionally XGBoost (if installed)

Notes
- This script is intentionally decoupled from the Java-equivalence pipeline.
- Goal: convergence and practicality, not parameter identity.
- See docs in src_py/docs/tutorials/training_tutorial.md for dataset preparation guidance.

Example
python src_py/scripts/training/train_baselines.py \
  --train-features path/to/X_train.csv \
  --train-labels   path/to/y_train.csv \
  --test-features  path/to/X_test.csv  \
  --test-labels    path/to/y_test.csv  \
  --out-dir        src_py/baselines/default_rf \
  --algo           sklearn_rf \
  --n-estimators   200 --max-depth 20 --seed 42
"""
import argparse
import json
import os
from pathlib import Path
from typing import Optional, Tuple

import joblib
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import (
        roc_auc_score,
        average_precision_score,
        accuracy_score,
        f1_score,
        log_loss,
    )
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

# xgboost is optional
try:
    import xgboost as xgb  # type: ignore
    XGB_AVAILABLE = True
except Exception:
    XGB_AVAILABLE = False


def load_csv_matrix(csv_path: Path) -> np.ndarray:
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            # skip header if first line contains non-numeric tokens
            if i == 0:
                parts = [p.strip() for p in line.split(",")]
                try:
                    _ = float(parts[0])
                except Exception:
                    continue
            parts = [p.strip() for p in line.split(",")]
            try:
                rows.append([float(x) for x in parts])
            except Exception:
                continue
    if not rows:
        raise ValueError(f"No numeric rows parsed from: {csv_path}")
    return np.asarray(rows, dtype=np.float64)


def load_csv_labels(csv_path: Path) -> np.ndarray:
    vals = []
    with open(csv_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            if i == 0:
                # header detection
                try:
                    _ = float(line.split(",")[0].strip())
                except Exception:
                    continue
            try:
                vals.append(float(line.split(",")[0].strip()))
            except Exception:
                continue
    if not vals:
        raise ValueError(f"No labels parsed from: {csv_path}")
    # interpret as binary labels if values are 0/1; otherwise probabilities/regression targets
    return np.asarray(vals, dtype=np.float64)


def train_sklearn_rf(
    X: np.ndarray,
    y: np.ndarray,
    n_estimators: int,
    max_depth: Optional[int],
    max_features: str,
    n_jobs: int,
    seed: int,
    verbose: bool,
) -> RandomForestClassifier:
    if not SKLEARN_AVAILABLE:
        raise ImportError("scikit-learn not available")
    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        max_features=max_features,
        n_jobs=n_jobs,
        random_state=seed,
        bootstrap=True,
        verbose=1 if verbose else 0,
    )
    from sklearn.utils import shuffle
    X, y = shuffle(X, y, random_state=seed)
    print(f'[train] sklearn_rf: n={X.shape[0]} d={X.shape[1]} n_estimators={n_estimators} max_depth={max_depth}')
    clf.fit(X, y.astype(int))
    return clf


def train_xgboost(
    X: np.ndarray,
    y: np.ndarray,
    n_estimators: int,
    max_depth: int,
    learning_rate: float,
    subsample: float,
    colsample_bytree: float,
    seed: int,
    verbose: bool,
):
    if not XGB_AVAILABLE:
        raise ImportError("xgboost not available. pip install xgboost")
    clf = xgb.XGBClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        learning_rate=learning_rate,
        subsample=subsample,
        colsample_bytree=colsample_bytree,
        reg_lambda=1.0,
        objective="binary:logistic",
        eval_metric="logloss",
        n_jobs=os.cpu_count() or 1,
        random_state=seed,
        tree_method="hist",
        verbosity=1 if verbose else 0,
    )
    print(f'[train] xgboost: n={X.shape[0]} d={X.shape[1]} n_estimators={n_estimators} max_depth={max_depth} lr={learning_rate}')
    clf.fit(X, y.astype(int))
    return clf


def evaluate(clf, X: np.ndarray, y: np.ndarray) -> dict:
    y_true = y.astype(int)
    metrics = {}
    try:
        if hasattr(clf, "predict_proba"):
            y_proba = clf.predict_proba(X)[:, 1]
        elif hasattr(clf, "decision_function"):
            # scale to 0-1 via logistic if possible; else min-max
            z = clf.decision_function(X)
            zmin, zmax = float(np.min(z)), float(np.max(z))
            y_proba = (z - zmin) / (zmax - zmin + 1e-12)
        else:
            y_proba = clf.predict(X)
            y_proba = (y_proba - np.min(y_proba)) / (np.max(y_proba) - np.min(y_proba) + 1e-12)
        y_pred = (y_proba >= 0.5).astype(int)
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba)) if SKLEARN_AVAILABLE else None
        metrics["pr_auc"] = float(average_precision_score(y_true, y_proba)) if SKLEARN_AVAILABLE else None
        metrics["accuracy"] = float(accuracy_score(y_true, y_pred)) if SKLEARN_AVAILABLE else None
        metrics["f1"] = float(f1_score(y_true, y_pred)) if SKLEARN_AVAILABLE else None
        try:
            metrics["logloss"] = float(log_loss(y_true, y_proba))
        except Exception:
            metrics["logloss"] = None
    except Exception as e:
        metrics["error"] = f"evaluation failed: {e}"
    return metrics


def main():
    p = argparse.ArgumentParser(description="Train baseline models (non-equivalence line)")
    p.add_argument("--train-features", required=True, help="CSV of training features (rows=samples)")
    p.add_argument("--train-labels", required=True, help="CSV of training labels (single column)")
    p.add_argument("--test-features", help="CSV of test features")
    p.add_argument("--test-labels", help="CSV of test labels")
    p.add_argument("--out-dir", required=True, help="Output directory for model and report")
    p.add_argument("--algo", choices=["sklearn_rf", "xgboost"], default="sklearn_rf")
    p.add_argument("--n-estimators", type=int, default=200)
    p.add_argument("--max-depth", type=int, default=None)
    p.add_argument("--max-features", default="sqrt")
    p.add_argument("--learning-rate", type=float, default=0.1)
    p.add_argument("--subsample", type=float, default=0.8)
    p.add_argument("--colsample-bytree", type=float, default=0.8)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--n-jobs", type=int, default=os.cpu_count() or 1)
    p.add_argument("--verbose", action="store_true", help="Enable algorithm verbose output during training")
    args = p.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    X_train = load_csv_matrix(Path(args.train_features))
    y_train = load_csv_labels(Path(args.train_labels))

    if args.algo == "sklearn_rf":
        clf = train_sklearn_rf(
            X_train,
            y_train,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth,
            max_features=args.max_features,
            n_jobs=args.n_jobs,
            seed=args.seed,
            verbose=bool(args.verbose),
        )
    else:
        clf = train_xgboost(
            X_train,
            y_train,
            n_estimators=args.n_estimators,
            max_depth=args.max_depth or 8,
            learning_rate=args.learning_rate,
            subsample=args.subsample,
            colsample_bytree=args.colsample_bytree,
            seed=args.seed,
            verbose=bool(args.verbose),
        )

    report = {
        "algo": args.algo,
        "n_estimators": args.n_estimators,
        "max_depth": args.max_depth,
        "seed": args.seed,
        "train_shape": list(X_train.shape),
    }

    # Evaluate on test set if provided
    if args.test_features and args.test_labels:
        X_test = load_csv_matrix(Path(args.test_features))
        y_test = load_csv_labels(Path(args.test_labels))
        report["metrics_test"] = evaluate(clf, X_test, y_test)

    # Persist
    joblib.dump(clf, out_dir / "model.pkl")
    with open(out_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(json.dumps({"status": "ok", **report}, indent=2))


if __name__ == "__main__":
    main()
