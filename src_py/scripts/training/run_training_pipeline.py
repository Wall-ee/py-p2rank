#!/usr/bin/env python3
"""
One-click training pipeline (server-friendly):
- Export training vectors with Java traineval (dataset .ds)
- Convert ARFF to CSV
- Train baseline model (sklearn RF or XGBoost)
- Optional hold-out split and evaluation
- Produce a JSON report with paths and metrics

Example:
python src_py/scripts/training/run_training_pipeline.py \
  --dataset /data/p2rank-datasets/holo4k.ds \
  --work-dir /data/p2rank-work/holo4k_run \
  --algo sklearn_rf --n-estimators 300 --max-depth 22 --seed 42 --memory 64G
"""
import argparse
import json
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PY = ['python']


def run(cmd, cwd=None, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    print('RUN:', ' '.join(map(str, cmd)))
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr)
        raise RuntimeError(f'Command failed: {cmd}')
    return res


def main():
    p = argparse.ArgumentParser(description='One-click training pipeline')
    p.add_argument('--dataset', required=True, help='Path to *.ds dataset (e.g., holo4k.ds)')
    p.add_argument('--work-dir', required=True, help='Working directory (will store all artifacts)')
    p.add_argument('--algo', choices=['sklearn_rf', 'xgboost'], default='sklearn_rf')
    p.add_argument('--n-estimators', type=int, default=200)
    p.add_argument('--max-depth', type=int, default=20)
    p.add_argument('--max-features', default='sqrt')
    p.add_argument('--learning-rate', type=float, default=0.1)
    p.add_argument('--subsample', type=float, default=0.8)
    p.add_argument('--colsample-bytree', type=float, default=0.8)
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--memory', default='32G', help='Java -Xmx memory')
    p.add_argument('--holdout', type=float, default=0.2, help='Optional holdout ratio (0 disables split)')
    args = p.parse_args()

    work = Path(args.work_dir)
    work.mkdir(parents=True, exist_ok=True)

    # 1) Export vectors via Java traineval
    print('[1/4] Exporting training vectors via Java traineval ...')
    vec_dir = work / 'traineval'
    run(PY + [str(REPO_ROOT / 'src_py' / 'scripts' / 'training' / 'export_vectors_java.py'),
              '--dataset', args.dataset, '--out-dir', str(vec_dir), '--memory', args.memory, '--seed', str(args.seed), '--loop', '1'])

    # 2) Convert ARFF to CSV
    print('[2/4] Converting vectorsTrain.arff(.gz) to CSV ...')
    arff_gz = vec_dir / 'vectorsTrain.arff.gz'
    csv_dir = work / 'csv'
    run(PY + [str(REPO_ROOT / 'src_py' / 'scripts' / 'training' / 'arff_to_csv.py'),
              '--arff', str(arff_gz), '--out-dir', str(csv_dir)])

    # 3) Optionally split holdout
    trX = csv_dir / 'X_train.csv'
    trY = csv_dir / 'y_train.csv'
    teX = None
    teY = None
    if args.holdout and args.holdout > 0:
        print(f'[3/4] Creating hold-out split: {int((1-args.holdout)*100)}% train / {int(args.holdout*100)}% test ...')
        split_dir = work / 'split'
        split_dir.mkdir(parents=True, exist_ok=True)
        from sklearn.model_selection import train_test_split
        import numpy as np
        import csv
        X = np.loadtxt(trX, delimiter=',')
        y = np.loadtxt(trY, delimiter=',')
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=args.holdout, random_state=args.seed, stratify=y)
        def _w(arr, path):
            with open(path, 'w', newline='') as f:
                w = csv.writer(f)
                if arr.ndim == 1:
                    for v in arr:
                        w.writerow([int(v)])
                else:
                    for r in arr:
                        w.writerow([f'{v:.6f}' for v in r])
        _w(Xtr, split_dir / 'X_train.csv')
        _w(ytr, split_dir / 'y_train.csv')
        _w(Xte, split_dir / 'X_test.csv')
        _w(yte, split_dir / 'y_test.csv')
        trX, trY = split_dir / 'X_train.csv', split_dir / 'y_train.csv'
        teX, teY = split_dir / 'X_test.csv', split_dir / 'y_test.csv'

    # 4) Train baseline
    print('[4/4] Training baseline model and evaluating ...')
    out_model = work / 'model'
    cmd = PY + [str(REPO_ROOT / 'src_py' / 'scripts' / 'training' / 'train_baselines.py'),
                '--train-features', str(trX), '--train-labels', str(trY), '--out-dir', str(out_model),
                '--algo', args.algo, '--n-estimators', str(args.n_estimators), '--max-depth', str(args.max_depth), '--seed', str(args.seed)]
    if args.algo == 'sklearn_rf':
        cmd += ['--max-features', args.max_features]
    else:
        cmd += ['--learning-rate', str(args.learning_rate), '--subsample', str(args.subsample), '--colsample-bytree', str(args.colsample_bytree)]
    if teX and teY:
        cmd += ['--test-features', str(teX), '--test-labels', str(teY)]
    # always enable algorithm verbose unless user disables explicitly (we don't have a flag here, so default on)
    cmd += ['--verbose']
    res = run(cmd)

    # 5) Summarize
    report = {
        'dataset': args.dataset,
        'work_dir': str(work),
        'vectors_dir': str(vec_dir),
        'csv_dir': str(csv_dir),
        'model_dir': str(out_model),
        'algo': args.algo,
        'n_estimators': args.n_estimators,
        'max_depth': args.max_depth,
        'seed': args.seed,
    }
    meta = out_model / 'metadata.json'
    if meta.exists():
        with open(meta, 'r') as f:
            report['training'] = json.load(f)
    with open(work / 'REPORT.json', 'w') as f:
        json.dump(report, f, indent=2)
    print('[DONE] Pipeline finished. Report:')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
