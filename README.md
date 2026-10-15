# Heart disease prediction

Author: `2025ae05142`

AIMLCZG523 MLOps Assignment 1 on the BITS Prayogshala Linux VM.
Uses the UCI processed Cleveland dataset and compares Logistic Regression,
Random Forest, and RBF SVC with leakage-safe preprocessing and stratified CV.
This is coursework, not a medical diagnostic tool.

## Reproduce on the VM

Run from the repository root with Python 3.12. No cloud account is required.
Create an isolated environment (do not use `--system-site-packages`):

```sh
python3 -m venv .venv-phase4
.venv-phase4/bin/python -m pip install -r requirements.txt
.venv-phase4/bin/python -m pip check
.venv-phase4/bin/python src/data/download_heart.py
.venv-phase4/bin/python src/data/prepare.py
.venv-phase4/bin/python src/eda/explore.py
.venv-phase4/bin/python src/train/train.py
.venv-phase4/bin/python -m src.train.package
.venv-phase4/bin/python -m src.infer.predict --input examples/patient.json
```

The final command emits only a JSON list on stdout, with integer `prediction`
(0 = absent, 1 = present) and float `confidence` (probability of that predicted
class, between 0 and 1). The sample is a feature-only dataset record, not an
independent test case. Actual verified output is recorded in [progress](docs/PROGRESS.md).

The decision rule is **predict 1 when P(disease) > 0.5; otherwise predict 0**.
An exact tie, P(disease) = 0.5, returns class 0 with confidence 0.5:
`argmax` selects the first class in the validated class order `[0, 1]`.
This fixed threshold is not a clinically optimized decision threshold.

Training appends three local MLflow runs and a new uncalibrated champion registry
version each time. It writes [the comparison](reports/model_comparison.md) and
[MLflow summary](reports/mlflow_summary.md). SQLite `mlflow.db` and artifact
directory `mlruns/` are local, gitignored runtime state.

Packaging independently recomputes candidate selection, evaluates a sigmoid
calibrator around the selected **full** preprocessing/classifier pipeline with
five outer validation folds and five inner calibration folds, then fits the
final artifact on all rows. It writes:

- `models/heart_pipeline.joblib`: complete probability-capable sklearn pipeline;
- `models/heart_pipeline.json`: data/artifact hashes, versions, settings, and metrics;
- [calibration diagnostics](reports/calibration_summary.md) and its reliability figure.

Candidate selection already used the dataset, so nested calibration diagnostics
are post-selection estimates, not an unbiased final test or proof of clinical
calibration. The calibrated artifact's labels may differ from the original SVC.
Its new metrics are kept separate; packaging does not overwrite or re-register
the uncalibrated Phase 3 registry model.

## Python inference

```python
import json
from pathlib import Path
from src.infer.predict import predict_records

records = json.loads(Path("examples/patient.json").read_text())
predictions = predict_records(records)
```

Each record must contain exactly the 13 feature keys shown in the sample;
values must be finite numbers or `null` (`None` in Python). Missing feature
values are handled by fitted imputers; missing/extra keys, booleans, strings,
and non-finite values are errors. Prediction does not fit models, download data,
or access MLflow. CLI failures exit nonzero with an attributed stderr message.
The pipeline is loaded from `models/heart_pipeline.joblib`, relative to the
repository rather than the shell working directory. **Only load trusted locally
generated joblib/MLflow pickle artifacts**: deserialization can execute code.

## Phase boundaries

See [progress and verification evidence](docs/PROGRESS.md),
[design decisions](docs/DECISIONS.md), and [data provenance](docs/DATA.md).
Automated tests/CI, the serving API, Docker, Kubernetes, and monitoring belong to
later phases and are not claimed complete here.
