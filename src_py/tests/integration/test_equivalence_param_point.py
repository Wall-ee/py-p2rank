import csv
from pathlib import Path

import numpy as np
import pytest

from p2rank.ml.faster_forest import FlatBinaryForestPy

pytestmark = pytest.mark.pure

REPO_ROOT = Path(__file__).resolve().parents[3]
NPZ_DIR = REPO_ROOT / 'src_py' / 'converted_models_final'
FEAT_DIR = REPO_ROOT / 'distro' / 'test_output' / 'features'
POINT_SCORES_DIR = REPO_ROOT / 'distro' / 'test_output' / 'point_scores'


def _load_features(csv_path: Path) -> np.ndarray:
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        r = csv.reader(f)
        _ = next(r, [])
        for row in r:
            try:
                rows.append([float(x) for x in row])
            except Exception:
                continue
    return np.asarray(rows, dtype=np.float64)


def _load_scores(csv_path: Path) -> np.ndarray:
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


@pytest.mark.parametrize('npz_path', sorted(NPZ_DIR.glob('*_flatforest.npz')))
def test_point_equivalence_param(npz_path: Path):
    model_name = npz_path.stem.replace('_flatforest', '')

    # We use the canonical 1fbl features; strict comparison only for 'default'
    feat_csv = FEAT_DIR / '1fbl.csv'
    assert feat_csv.exists(), f'Missing features CSV: {feat_csv}'

    ff = FlatBinaryForestPy.load_npz(npz_path)
    X = _load_features(feat_csv)

    need = int(ff.arr.num_attributes)
    if X.shape[1] > need:
        X = X[:, :need]
    elif X.shape[1] < need:
        pad = np.zeros((X.shape[0], need - X.shape[1]), dtype=X.dtype)
        X = np.hstack([X, pad])

    py_scores = ff.predict(X)

    if model_name == 'default':
        gold_scores_csv = POINT_SCORES_DIR / '1fbl.csv'
        assert gold_scores_csv.exists(), f'Missing gold point scores CSV: {gold_scores_csv}'
        java_scores = _load_scores(gold_scores_csv)
        assert py_scores.shape == java_scores.shape
        diff = np.abs(py_scores - java_scores)
        assert float(diff.max()) < 1e-6, f'max diff={float(diff.max())}'
    else:
        # No gold for other models in repo; sanity only
        assert py_scores.shape[0] == X.shape[0]
        assert np.isfinite(py_scores).all()
        assert float(py_scores.min()) >= -1e-12
        assert float(py_scores.max()) <= 1.0 + 1e-12
