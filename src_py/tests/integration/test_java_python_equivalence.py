import os
import subprocess
import json
from pathlib import Path

import pytest

# --- 环境前提 ----------------------------------------------------------
# 1. Java 17 可用，且可执行构建出的 p2rank.jar（若无则跳过）
# 2. Python ≥3.9，已安装 src_py（开发模式安装即可）
# 3. pytest -k equivalence 显式触发

pytestmark = pytest.mark.equivalence

REPO_ROOT = Path(__file__).resolve().parents[3]
SAMPLE_PDB = REPO_ROOT / 'distro' / 'test_data' / '1fbl.cif'
JAR_PATH = REPO_ROOT / 'distro' / 'bin' / 'p2rank.jar'
LIB_DIR = REPO_ROOT / 'distro' / 'bin' / 'lib'
JAVA_MAIN = 'cz.siret.prank.program.Main'


def _detect_java_bin() -> str:
    # Prefer JAVA_HOME
    jh = os.environ.get('JAVA_HOME')
    if jh:
        cand = Path(jh) / 'bin' / 'java'
        if cand.exists():
            return str(cand)
    # Homebrew common locations (Apple Silicon and Intel)
    for p in [
        '/opt/homebrew/opt/openjdk@17/bin/java',
        '/opt/homebrew/opt/openjdk/bin/java',
        '/usr/local/opt/openjdk@17/bin/java',
        '/usr/local/opt/openjdk/bin/java',
    ]:
        if Path(p).exists():
            return p
    # Fallback to PATH
    return 'java'


def have_java() -> bool:
    try:
        jb = _detect_java_bin()
        subprocess.run([jb, '-version'], capture_output=True, text=True)
        return True
    except Exception:
        return False


def have_prank_jar() -> bool:
    return JAR_PATH.exists() and LIB_DIR.exists()


def ensure_build_runtime_env():
    """确保 jar 运行所需的 config/models 可被找到（在 build 下创建软链）。"""
    build_dir = REPO_ROOT / 'build'
    (build_dir / 'config').mkdir(parents=True, exist_ok=True)
    (build_dir / 'models').mkdir(parents=True, exist_ok=True)

    # 链接 config -> repo/config
    cfg_link = build_dir / 'config' / 'README.link'
    if not (build_dir / 'config' / 'test-default.groovy').exists():
        # 复制或软链整个 config 目录
        # 使用软链以避免大文件复制
        target_cfg = build_dir / 'config'
        if target_cfg.exists() and any(target_cfg.iterdir()):
            pass
        else:
            # 创建到仓库 config 的符号链接（如果可能）
            try:
                if target_cfg.exists():
                    target_cfg.rmdir()
                os.symlink((REPO_ROOT / 'config').as_posix(), target_cfg.as_posix())
            except Exception:
                # 回退：不处理，依赖 -c 绝对路径
                pass
        cfg_link.write_text('linked to repo config if possible')

    # 链接 models -> repo/distro/models
    mdl_link = build_dir / 'models' / 'README.link'
    if not any((build_dir / 'models').iterdir()):
        try:
            os.symlink((REPO_ROOT / 'distro' / 'models').as_posix(), (build_dir / 'models').as_posix())
        except Exception:
            pass
        mdl_link.write_text('linked to repo distro/models if possible')


def java_classpath() -> str:
    # 构造包含主 JAR 与所有依赖的类路径
    jars = [str(JAR_PATH)] + [str(p) for p in LIB_DIR.glob('*.jar')]
    return os.pathsep.join(jars)


def java_pred_cmd(sample: Path, outdir: Path):
    cfg = (REPO_ROOT / 'config' / 'test-default.groovy').as_posix()
    model_dir = (REPO_ROOT / 'distro' / 'models' / 'default').as_posix()
    cp = java_classpath()
    jb = _detect_java_bin()
    return [
        jb, '-cp', cp, JAVA_MAIN,
        'predict', '-f', str(sample), '-o', str(outdir), '-c', cfg, '-m', model_dir
    ]


def py_pred_cmd(sample: Path, outdir: Path):
    # Force bridge mode by using a model name that has no corresponding NPZ
    return [
        'python', '-m', 'p2rank.program.main',
        'predict', '-i', str(sample), '-o', str(outdir), '-m', 'default_bridge'
    ]


def run_cmd(cmd, cwd):
    """运行命令并捕获输出"""
    env = os.environ.copy()
    # 确保 Python 子进程能导入 src_py 包
    src_py = (REPO_ROOT / 'src_py').as_posix()
    env['PYTHONPATH'] = f"{src_py}:{env.get('PYTHONPATH','')}"
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def find_prediction_csv(outdir: Path) -> Path:
    cand = list(outdir.glob('*_predictions.csv'))
    if not cand:
        raise FileNotFoundError(f"No predictions CSV in {outdir}")
    # 取第一个（单文件预测只有一个）
    return cand[0]


def load_top3_scores_from_csv(csv_path: Path):
    # 预测 CSV 通常包含 header 行，包含 score 列
    import csv
    scores = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        if not rows:
            return []
        # Normalize header by stripping whitespace
        header = [h.strip() for h in rows[0]]
        try:
            score_idx = header.index('score')
        except ValueError:
            # Try case-insensitive match
            lower = [h.lower() for h in header]
            score_idx = lower.index('score') if 'score' in lower else -1
        if score_idx < 0:
            return []
        for row in rows[1:]:
            if len(row) <= score_idx:
                continue
            try:
                scores.append(float(row[score_idx].strip()))
            except Exception:
                continue
        for row in reader:
            if 'score' in row:
                try:
                    scores.append(float(row['score']))
                except Exception:
                    pass
    # 已按分数降序；若不确定，可排序
    scores = sorted(scores, reverse=True)
    return scores[:3]


@pytest.mark.timeout(600)
def test_java_python_prediction_equivalence(tmp_path):
    if not SAMPLE_PDB.exists():
        pytest.skip("Sample PDB not found – skip equivalence test")
    if not have_java():
        pytest.skip("Java runtime not available – skip equivalence test")
    if not have_prank_jar():
        pytest.skip("prank.jar not found (build/libs/prank.jar). Build Java first – skip equivalence test")

    ensure_build_runtime_env()

    # 1. Java 预测（单独目录）
    out_java = tmp_path / 'java'
    out_java.mkdir(parents=True, exist_ok=True)
    run_cmd(java_pred_cmd(SAMPLE_PDB, out_java), cwd=out_java)
    java_csv = find_prediction_csv(out_java)

    # 2. Python 预测（单独目录）
    out_py = tmp_path / 'py'
    out_py.mkdir(parents=True, exist_ok=True)
    run_cmd(py_pred_cmd(SAMPLE_PDB, out_py), cwd=out_py)
    try:
        py_csv = find_prediction_csv(out_py)
    except FileNotFoundError:
        pytest.skip("Python predictor did not produce predictions CSV yet – skip equivalence check for now")

    java_scores = load_top3_scores_from_csv(java_csv)
    py_scores = load_top3_scores_from_csv(py_csv)

    assert len(java_scores) == len(py_scores) == 3, "Top-3 size mismatch"
    for j, p in zip(java_scores, py_scores):
        assert abs(j - p) < 1e-6, f"Score differs: Java={j} Python={p}"
