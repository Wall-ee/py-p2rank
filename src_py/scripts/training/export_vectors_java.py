#!/usr/bin/env python3
"""
Export P2Rank training vectors (ARFF) using Java traineval.

- Detects Java and classpath automatically
- Runs: Main traineval -t <dataset> -e <dataset> -delete_vectors 0 -delete_models 0
- Writes vectorsTrain.arff.gz into the output directory

Example:
python src_py/scripts/training/export_vectors_java.py \
  --dataset /Users/you/p2rank-datasets/holo4k.ds \
  --out-dir /path/to/out/holo4k_traineval \
  --memory 32G --seed 42
"""
import argparse
import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
JAR_PATH = REPO_ROOT / 'distro' / 'bin' / 'p2rank.jar'
LIB_DIR = REPO_ROOT / 'distro' / 'bin' / 'lib'
JAVA_MAIN = 'cz.siret.prank.program.Main'


def detect_java_bin() -> str:
    jh = os.environ.get('JAVA_HOME')
    if jh:
        cand = Path(jh) / 'bin' / 'java'
        if cand.exists():
            return str(cand)
    for p in [
        '/opt/homebrew/opt/openjdk@17/bin/java',
        '/opt/homebrew/opt/openjdk/bin/java',
        '/usr/local/opt/openjdk@17/bin/java',
        '/usr/local/opt/openjdk/bin/java',
    ]:
        if Path(p).exists():
            return p
    return 'java'


def build_classpath() -> str:
    jars = [str(JAR_PATH)] + [str(p) for p in LIB_DIR.glob('*.jar')]
    return os.pathsep.join(jars)


def run_traineval(dataset: Path, out_dir: Path, memory: str, seed: int, loop: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    java_bin = detect_java_bin()
    cp = build_classpath()
    cmd = [
        java_bin, f'-Xmx{memory}', '-cp', cp, JAVA_MAIN,
        'traineval', '-t', str(dataset), '-e', str(dataset),
        '-o', str(out_dir),
        '-delete_vectors', '0',
        '-delete_models', '0',
        '-fail_fast', 'true',
        '-loop', str(loop),
        '-seed', str(seed),
    ]
    env = os.environ.copy()
    result = subprocess.run(cmd, capture_output=True, text=True, env=env)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
    return result.returncode


def main():
    p = argparse.ArgumentParser(description='Export training vectors via Java traineval')
    p.add_argument('--dataset', required=True, help='Path to *.ds dataset (e.g., holo4k.ds)')
    p.add_argument('--out-dir', required=True, help='Output directory')
    p.add_argument('--memory', default='32G', help='Java -Xmx memory (default: 32G)')
    p.add_argument('--seed', type=int, default=42)
    p.add_argument('--loop', type=int, default=1)
    args = p.parse_args()

    rc = run_traineval(Path(args.dataset), Path(args.out_dir), args.memory, args.seed, args.loop)
    if rc != 0:
        raise SystemExit(rc)


if __name__ == '__main__':
    main()
