import numpy as np
import pytest
from pathlib import Path

pytestmark = pytest.mark.pure

REPO_ROOT = Path(__file__).resolve().parents[3]
NPZ_DIR = REPO_ROOT / 'src_py' / 'converted_models_final'

@pytest.mark.parametrize('npz_path', sorted(NPZ_DIR.glob('*_flatforest.npz')))
def test_npz_model_predicts(npz_path: Path):
    from p2rank.ml.faster_forest import FlatBinaryForestPy

    ff = FlatBinaryForestPy.load_npz(npz_path)
    num_attr = int(ff.arr.num_attributes)
    assert num_attr > 0

    rng = np.random.default_rng(0)
    X = rng.normal(size=(64, num_attr)).astype(np.float64)

    y = ff.predict(X)
    assert y.shape == (64,)
    assert np.isfinite(y).all()
    assert float(y.min()) >= -1e-12
    assert float(y.max()) <= 1.0 + 1e-12
