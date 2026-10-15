# MLflow summary - Author: `2025ae05142`

- Tracking and registry URI: `sqlite:////home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction/mlflow.db`
- Experiment: `heart-disease-2025ae05142` (ID `1`).
- Artifact store: `file:///home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction/mlruns`
- Dataset SHA-256: `655b46ed75efcb7eb0f636b952f6ed68c6bf48487c6dbde7070ade6a3d5390d8`
- Metrics are held-out CV means and sample standard deviations; logged pipelines are subsequently fit on all 303 rows.

| Model | Run ID | Model URI |
|---|---|---|
| logistic_regression | `36f54d74d4604552aaeec49ca8e4dd5c` | `models:/m-3286e58d035343758e4f88254a6ae92c` |
| random_forest | `f1fd9806c995443db667aee24e95dd87` | `models:/m-1255fc7c3069418892c1b4d88ef4d9bc` |
| rbf_svc | `b31ee47545d04752a9bd7f9b9f7b1b9c` | `models:/m-966e916d44dc4c95af24d96d059042d1` |

- Champion: `rbf_svc`; run ID: `b31ee47545d04752a9bd7f9b9f7b1b9c`.
- Registered model: `heart-disease-champion-2025ae05142`, version `1`.
- Registry URI: `models:/heart-disease-champion-2025ae05142/1`
- Each run contains parameters, all four CV metrics and standard deviations, the complete fitted sklearn pipeline, three EDA figures, and the comparison report.
- The champion is not calibrated and does not expose confidence probabilities. The confidence plan in docs/DECISIONS.md must be implemented and evaluated before packaging a confidence-bearing inference artifact in Phase 4.

Reproduce: `python3 src/train/train.py` from the repository root. Each execution appends runs and a new registry version; the summary records the latest successful batch.
