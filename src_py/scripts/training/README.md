# Baseline training (non-equivalence line)

This folder contains minimal, reproducible scripts to train new Python-native models that do not aim for Java parameter equivalence. They use the same datasets/targets but different algorithms (sklearn RF, optional XGBoost). Suitable for future GPU/deep learning pipelines.

Key scripts:
- export_vectors_java.py: export training vectors via Java traineval (produces vectorsTrain.arff.gz).
- arff_to_csv.py: convert vectorsTrain.arff(.gz) to CSV features/labels.
- train_baselines.py: train RandomForest (scikit-learn) or XGBoost and write model.pkl + metadata.json.
- run_training_pipeline.py: one-click orchestrator (export -> convert -> train -> optional eval -> REPORT.json).

End-to-end (holo4k example):
```
# 1) export vectors via Java
python src_py/scripts/training/export_vectors_java.py \
  --dataset /Users/you/p2rank-datasets/holo4k.ds \
  --out-dir /path/to/work/holo4k_traineval --memory 64G --seed 42

# 2) convert ARFF to CSV
python src_py/scripts/training/arff_to_csv.py \
  --arff /path/to/work/holo4k_traineval/vectorsTrain.arff.gz \
  --out-dir /path/to/work/holo4k_csv

# 3) train + evaluate (if you have a split)
python src_py/scripts/training/train_baselines.py \
  --train-features /path/to/work/holo4k_csv/X_train.csv \
  --train-labels   /path/to/work/holo4k_csv/y_train.csv \
  --out-dir        /path/to/work/holo4k_rf \
  --algo           sklearn_rf --n-estimators 300 --max-depth 22 --seed 42

# or one-click
python src_py/scripts/training/run_training_pipeline.py \
  --dataset /Users/you/p2rank-datasets/holo4k.ds \
  --work-dir /path/to/work/holo4k_run \
  --algo sklearn_rf --n-estimators 300 --max-depth 22 --seed 42 --memory 64G --holdout 0.2
```

Notes:
- This line is isolated from equivalence tests; using it will not affect FasterForest .npz inference or Java parity.
- To enable XGBoost: `pip install xgboost` and set `--algo xgboost` in the commands.

Why exporting vectors via Java traineval:
- P2Rank feature/label generation follows the full Java pipeline (SAS sampling, positive/negative definitions, thresholds and filtering, denoising, possible decoy negatives, etc.). Using Java traineval to produce vectorsTrain.arff.gz gives the authoritative training data format and avoids divergence from re-implementing the whole pipeline in Python. This way, Python baselines evaluate the learning algorithm (RF/XGB) itself without mixing inconsistencies from a different feature pipeline. We can replace this step later when a full Python data pipeline is ready.

