import csv
from pathlib import Path

import numpy as np
import pytest

from p2rank.ml.faster_forest import FlatBinaryForestPy


pytestmark = pytest.mark.pure


REPO_ROOT = Path(__file__).resolve().parents[3]
FEAT_CSV = REPO_ROOT / 'distro' / 'test_output' / 'features' / '1fbl.csv'
POINT_SCORES_CSV = REPO_ROOT / 'distro' / 'test_output' / 'point_scores' / '1fbl.csv'
NPZ = REPO_ROOT / 'src_py' / 'converted_models_final' / 'default_flatforest.npz'  # fasterforest flattened arrays


def load_features(csv_path: Path) -> np.ndarray:
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        r = csv.reader(f)
        header = next(r, [])
        for row in r:
            try:
                rows.append([float(x) for x in row])
            except Exception:
                continue
    return np.asarray(rows, dtype=np.float64)


def load_scores(csv_path: Path) -> np.ndarray:
    scores = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        r = csv.reader(f)
        _ = next(r, [])
        for row in r:
            try:
                scores.append(float(row[0]))
            except Exception:
                continue
    return np.asarray(scores, dtype=np.float64)


def test_point_level_equivalence_default_model():
    assert FEAT_CSV.exists(), f'Missing features CSV: {FEAT_CSV}'
    assert POINT_SCORES_CSV.exists(), f'Missing java point scores CSV: {POINT_SCORES_CSV}'
    assert NPZ.exists(), f'Missing NPZ model: {NPZ}'

    ff = FlatBinaryForestPy.load_npz(NPZ)
    X = load_features(FEAT_CSV)
    # align feature dimension
    need = int(ff.arr.num_attributes)
    if X.shape[1] > need:
        X = X[:, :need]
    elif X.shape[1] < need:
        pad = np.zeros((X.shape[0], need - X.shape[1]), dtype=X.dtype)
        X = np.hstack([X, pad])

    py_scores = ff.predict(X)
    java_scores = load_scores(POINT_SCORES_CSV)
    assert py_scores.shape == java_scores.shape

    # strict equivalence
    diff = np.abs(py_scores - java_scores)
    assert float(diff.max()) < 1e-6, f'max diff={float(diff.max())}'

