# MLflow summary - Author: `2025ae05142`

- Tracking and registry URI: `sqlite:////home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction/mlflow.db`
- Experiment: `heart-disease-2025ae05142` (ID `1`).
- Artifact store: `file:///home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction/mlruns`
- Dataset SHA-256: `655b46ed75efcb7eb0f636b952f6ed68c6bf48487c6dbde7070ade6a3d5390d8`
- Metrics are held-out CV means and sample standard deviations; logged pipelines are subsequently fit on all 303 rows.

| Model | Run ID | Model URI |
|---|---|---|
| logistic_regression | `e31403f4bb7d4506b39ceb1ff05004c4` | `models:/m-b5fd21e8ba934af496d60383792f11d2` |
| random_forest | `278a020c22ae4530aabafb6bd5fc1307` | `models:/m-01a5af4d0b6c48ce82d5cea6cbb03c72` |
| rbf_svc | `5ad5e00bd4714b998beb1b868379a2b2` | `models:/m-bfd6e6c8994c44298d525deb69be3746` |

- Champion: `rbf_svc`; run ID: `5ad5e00bd4714b998beb1b868379a2b2`.
- Registered model: `heart-disease-champion-2025ae05142`, version `2`.
- Registry URI: `models:/heart-disease-champion-2025ae05142/2`
- Each run contains parameters, all four CV metrics and standard deviations, the complete fitted sklearn pipeline, three EDA figures, and the comparison report.
- The registered champion is the uncalibrated candidate pipeline, not the calibrated serving artifact; its CV metrics describe that uncalibrated model.
- Separate serving-artifact workflow: `python -m src.train.package` evaluates and writes the calibrated pipeline to `models/heart_pipeline.joblib` with provenance and `reports/calibration_summary.md`. This training command does not run packaging or verify that those outputs exist or match this run. Consult the packaging provenance and calibration report for its actual results; packaging does not replace this registry version.

Reproduce: `python3 src/train/train.py` from the repository root. Each execution appends runs and a new registry version; the summary records the latest successful batch.
