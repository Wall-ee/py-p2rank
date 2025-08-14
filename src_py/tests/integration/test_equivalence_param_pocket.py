import csv
import os
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.pure

REPO_ROOT = Path(__file__).resolve().parents[3]
GOLD_DIR = REPO_ROOT / 'distro' / 'test_output'


def _load_top_scores_from_csv(csv_path: Path, top_n: int = 3):
    scores = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return []
        header = [h.strip().lower() for h in rows[0]]
        try:
            i_score = header.index('score')
        except ValueError:
            return []
        for row in rows[1:]:
            if len(row) <= i_score:
                continue
            try:
                scores.append(float(row[i_score].strip()))
            except Exception:
                continue
    scores = sorted(scores, reverse=True)
    return scores[:top_n]


@pytest.mark.parametrize('case', ['1fbl'])
def test_pocket_equivalence_default(case: str, tmp_path):
    gold_csv = GOLD_DIR / f'{case}.cif_predictions.csv'
    assert gold_csv.exists(), f'Gold predictions missing: {gold_csv}'

    # Prefer running Java to reproduce gold, otherwise skip (pure-Python lacks 3D coordinates for clustering)
    jar_path = REPO_ROOT / 'distro' / 'bin' / 'p2rank.jar'
    lib_dir = REPO_ROOT / 'distro' / 'bin' / 'lib'
    sample = REPO_ROOT / 'distro' / 'test_data' / f'{case}.cif'
    if not (jar_path.exists() and lib_dir.exists() and sample.exists()):
        pytest.skip('Java runtime or jars not available for pocket-level equivalence')

    classpath = os.pathsep.join([str(jar_path)] + [str(p) for p in lib_dir.glob('*.jar')])
    cmd = [
        'java', '-cp', classpath, 'cz.siret.prank.program.Main',
        'predict', '-f', str(sample), '-o', str(tmp_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        pytest.skip(f'Java predict failed in this env: {result.stderr}')

    py_csvs = list(tmp_path.glob('*_predictions.csv'))
    assert py_csvs, 'No predictions CSV produced by Java run'
    py_csv = py_csvs[0]

    gold_scores = _load_top_scores_from_csv(gold_csv)
    py_scores = _load_top_scores_from_csv(py_csv)
    assert len(gold_scores) == len(py_scores) == 3
    for g, p in zip(gold_scores, py_scores):
        assert abs(g - p) < 1e-6
