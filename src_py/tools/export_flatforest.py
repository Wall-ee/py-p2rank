#!/usr/bin/env python3
"""
Export FlatBinaryForest arrays from Java model to NPZ for pure-Python inference.

Requires Java distro built at `distro/bin/p2rank.jar` and deps in `distro/bin/lib`.
"""
import os
import glob
import argparse
from pathlib import Path
import numpy as np


def start_jvm_with_distro(repo_root: Path):
    import jpype
    if jpype.isJVMStarted():
        return
    jars = [str(repo_root / 'distro' / 'bin' / 'p2rank.jar')] + \
           glob.glob(str(repo_root / 'distro' / 'bin' / 'lib' / '*.jar'))
    jpype.startJVM(classpath=[os.pathsep.join(jars)])


def export_model_npz(model_dir: Path, out_npz: Path):
    import jpype
    from jpype import JClass
    import numpy as np

    Futils = JClass('cz.siret.prank.utils.Futils')
    WekaUtils = JClass('cz.siret.prank.utils.WekaUtils')
    FlatBinaryForest = JClass('cz.siret.prank.fforest.api.FlatBinaryForest')
    ModelConverter = JClass('cz.siret.prank.program.ml.ModelConverter')
    Model = JClass('cz.siret.prank.program.ml.Model')

    model_zst = model_dir / 'model.zst'
    if not model_zst.exists():
        raise FileNotFoundError(f"model.zst not found in {model_dir}")

    is_ = Futils.inputStream(str(model_zst))
    clf = WekaUtils.loadClassifier(is_)
    if not isinstance(clf, FlatBinaryForest):
        m = Model('tmp', clf)
        m2 = ModelConverter().applyConversions(m)
        clf = m2.classifier

    # Reflection to access protected arrays
    def find_field(field_name: str):
        c = clf.getClass()
        while c is not None:
            try:
                f = c.getDeclaredField(field_name)
                f.setAccessible(True)
                return f
            except Exception:
                c = c.getSuperclass()
        raise AttributeError(f"Field not found in class hierarchy: {field_name}")

    def get_int_array(field_name: str) -> np.ndarray:
        f = find_field(field_name)
        jarr = f.get(clf)
        return np.array(list(jarr), dtype=np.int64)

    def get_double_array(field_name: str) -> np.ndarray:
        f = find_field(field_name)
        jarr = f.get(clf)
        return np.array(list(jarr), dtype=np.float64)

    child_left = get_int_array('childLeft')
    child_right = get_int_array('childRight')
    feature_index = get_int_array('attributeIndex')
    threshold = get_double_array('splitPoint')
    # Build per-node positive-class probability (node_prob) from classProbs
    # Prefer direct 'score' array if available; fallback to classProbs
    node_prob = None
    leaf_class0 = None
    leaf_class1 = None
    c = clf.getClass(); score_f = None
    while c is not None and score_f is None:
        try:
            score_f = c.getDeclaredField('score')
        except Exception:
            c = c.getSuperclass()
    if score_f is not None:
        score_f.setAccessible(True)
        jarr = score_f.get(clf)
        if jarr is not None:
            node_prob = np.array(list(jarr), dtype=np.float64)
    if node_prob is None:
        c = clf.getClass(); f = None
        while c is not None and f is None:
            try:
                f = c.getDeclaredField('classProbs')
            except Exception:
                c = c.getSuperclass()
        if f is not None:
            f.setAccessible(True)
            j2d = f.get(clf)
            outer_len = len(j2d)
            node_prob = np.zeros(outer_len, dtype=np.float64)
            leaf_class0 = np.zeros(outer_len, dtype=np.float64)
            leaf_class1 = np.zeros(outer_len, dtype=np.float64)
            for lid in range(outer_len):
                row = j2d[lid]
                if row is None:
                    continue
                prow = np.array(list(row), dtype=np.float64)
                if prow.size >= 2:
                    leaf_class0[lid] = float(prow[0])
                    leaf_class1[lid] = float(prow[1])
                    s = leaf_class0[lid] + leaf_class1[lid]
                    node_prob[lid] = float(leaf_class1[lid] / s) if s > 0 else 0.0
                elif prow.size == 1:
                    leaf_class0[lid] = float(1.0 - prow[0])
                    leaf_class1[lid] = float(prow[0])
                    node_prob[lid] = float(prow[0])

    num_trees = int(clf.getNumTrees())
    # numAttributes on LegacyFlatBinaryForest counts class column as well; we need feature count
    # Derive from attributeIndex max + 1 to get true feature dimension
    derived_num_attributes = int(np.max(feature_index) + 1) if feature_index.size > 0 else 0
    num_attributes = derived_num_attributes

    # Derive roots and leaf ids
    n = child_left.shape[0]
    all_idx = np.arange(n, dtype=np.int64)
    children = np.concatenate([child_left[child_left >= 0], child_right[child_right >= 0]])
    roots = np.setdiff1d(all_idx, np.unique(children))
    # In LegacyFlatBinaryForest bytecode, leaf access uses classProbs[-i] when i<0 (no -1 offset)
    left_leaf_id = np.where(child_left < 0, (-child_left).astype(np.int64), np.int64(-1))
    right_leaf_id = np.where(child_right < 0, (-child_right).astype(np.int64), np.int64(-1))

    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_npz,
        child_left=child_left,
        child_right=child_right,
        feature_index=feature_index,
        threshold=threshold,
        node_prob=node_prob,
        leaf_class0=leaf_class0,
        leaf_class1=leaf_class1,
        left_leaf_id=left_leaf_id,
        right_leaf_id=right_leaf_id,
        num_trees=num_trees,
        num_attributes=num_attributes,
        roots=roots,
    )


def main():
    parser = argparse.ArgumentParser(description='Export FlatBinaryForest arrays to NPZ')
    parser.add_argument('--repo-root', default=str(Path(__file__).resolve().parents[2]), help='Repository root')
    parser.add_argument('--model-dir', required=True, help='Path to model directory (contains model.zst)')
    parser.add_argument('--out-npz', required=True, help='Output NPZ path')
    args = parser.parse_args()

    repo_root = Path(args.repo_root)
    start_jvm_with_distro(repo_root)
    export_model_npz(Path(args.model_dir), Path(args.out_npz))
    print(f"NPZ exported to {args.out_npz}")


if __name__ == '__main__':
    main()


