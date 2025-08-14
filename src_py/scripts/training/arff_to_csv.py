#!/usr/bin/env python3
"""
Convert P2Rank vectorsTrain.arff(.gz) to CSV feature/label files usable by Python training.

Example:
python src_py/scripts/training/arff_to_csv.py \
  --arff /path/to/vectorsTrain.arff.gz \
  --out-dir src_py/baselines/holo4k
"""
import argparse
import gzip
from pathlib import Path
import csv
from scipy.io import arff
import numpy as np


def write_csv(matrix, path: Path):
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        if matrix.ndim == 1:
            for v in matrix:
                w.writerow([int(v)])
        else:
            for r in matrix:
                w.writerow([f'{v:.6f}' for v in r])


def main():
    p = argparse.ArgumentParser(description='Convert vectorsTrain.arff(.gz) to CSVs')
    p.add_argument('--arff', required=True, help='Path to vectorsTrain.arff or .gz')
    p.add_argument('--out-dir', required=True, help='Output directory for X_train.csv and y_train.csv')
    args = p.parse_args()

    arff_path = Path(args.arff)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if arff_path.suffix == '.gz':
        raw = out_dir / (arff_path.stem)  # remove .gz
        with gzip.open(arff_path, 'rb') as g, open(raw, 'wb') as f:
            f.write(g.read())
        load_path = raw
    else:
        load_path = arff_path

    data, meta = arff.loadarff(str(load_path))
    names = list(meta.names())
    cls_name = None
    for cand in ['class', 'Class', 'label', 'y']:
        if cand in names:
            cls_name = cand
            break
    if cls_name is None:
        cls_name = names[-1]
    X_cols = [n for n in names if n != cls_name]

    X = []
    y = []
    for row in data:
        X.append([float(row[n]) for n in X_cols])
        yv = row[cls_name]
        if isinstance(yv, (bytes, bytearray)):
            yv = yv.decode('utf-8')
        try:
            y.append(int(float(yv)))
        except Exception:
            y.append(1 if str(yv).strip().lower() in ('true', 't', 'yes', 'y', 'pos', 'positive', '1') else 0)

    X = np.asarray(X, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    write_csv(X, out_dir / 'X_train.csv')
    write_csv(y, out_dir / 'y_train.csv')

    print(f'Saved: {out_dir}/X_train.csv {out_dir}/y_train.csv shape={X.shape}')


if __name__ == '__main__':
    main()
