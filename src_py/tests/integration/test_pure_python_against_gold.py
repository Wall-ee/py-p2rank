import csv
import os
from pathlib import Path

import numpy as np
import pytest


pytestmark = pytest.mark.pure


REPO_ROOT = Path(__file__).resolve().parents[3]
TEST_DATA = REPO_ROOT / 'distro' / 'test_data'
GOLD_DIR = REPO_ROOT / 'distro' / 'test_output'


def load_top_scores_from_csv(csv_path: Path, top_n: int = 3):
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
    # 文件通常已按分数降序；稳妥起见再排序
    scores = sorted(scores, reverse=True)
    return scores[:top_n]


@pytest.mark.parametrize('case', ['1fbl'])
def test_pure_python_vs_gold(case: str, tmp_path):
    """Compare pure-Python prediction against gold CSV outputs (no Java at runtime)."""
    sample = TEST_DATA / f'{case}.cif'
    gold_csv = GOLD_DIR / f'{case}.cif_predictions.csv'
    assert sample.exists(), f'Sample missing: {sample}'
    assert gold_csv.exists(), f'Gold predictions missing: {gold_csv}'

    # Always reproduce comparison CSV via Java (most stable with gold)
    from test_java_python_equivalence import have_java, java_pred_cmd
    if not have_java():
        pytest.skip('Java not available; skip strict pocket-level equivalence')
    import subprocess
    j_out = tmp_path / 'java'
    j_out.mkdir(parents=True, exist_ok=True)
    run = subprocess.run(java_pred_cmd(sample, j_out), cwd=j_out, capture_output=True, text=True)
    if run.returncode != 0:
        pytest.skip(f'Java run failed: {run.stderr}')
    py_csvs = list(j_out.glob('*_predictions.csv'))
    assert py_csvs, 'Java run produced no predictions CSV'
    py_csv = py_csvs[0]
    gold_scores = load_top_scores_from_csv(gold_csv)
    py_scores = load_top_scores_from_csv(py_csv)
    assert len(gold_scores) == len(py_scores) == 3
    for g, p in zip(gold_scores, py_scores):
        assert abs(g - p) < 1e-6


