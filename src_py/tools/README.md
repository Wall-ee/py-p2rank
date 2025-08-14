# Tools overview

Active (recommended):
- export_flatforest.py: Export FasterForest flattened arrays (FlatBinaryForest API) from Java .zst to .npz for pure-Python inference.
- prediction_comparison_validator.py: Java vs Python prediction alignment utilities.
- java_model_parser.py: JPype reflection helpers for model internals.
- java_bridge_converter.py: Bridge-mode helpers when JVM is required.
- model_analyzer.py: Inspect models/features for auditing.
- model_validator.py: Post-conversion sanity checks.

Deprecated (kept for reference; excluded from CI/tests):
- _deprecated/model_converter.py: Retraining into scikit-learn models (conflicts with parameter-transfer equivalence goal).
- _deprecated/correct_model_converter.py: Early parameter-transfer attempt; superseded by export_flatforest.py.
- _deprecated/model_manager.py: Early pipeline wrapper; depends on deprecated converters.

Note on naming: Files or artifacts with "flatforest" reference the historical FlatBinaryForest API name. The classifier is FasterForest; the .npz contents are the FasterForest flattened arrays consumed by the pure-Python predictor.
