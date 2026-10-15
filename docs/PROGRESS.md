# Assignment progress

Author: `2025ae05142`

Complete one phase at a time. A phase is complete only when its gate is met; record blockers and evidence here.

| Phase | Status | Gate / evidence |
|---|---|---|
| 0 — Lab baseline | pass | `docs/ENVIRONMENT.md` records the Linux VM baseline. Python 3.12.9 satisfies the >=3.10 gate; Docker and Minikube are installed. GitHub Actions API access returned HTTP 200; workflow execution remains unverified until Phase 5. |
| 1 — Data and EDA | pass | UCI download, preparation, and EDA commands succeeded; 303 rows, target counts 164/139, 6 reported missing feature values, summary, and all three figures verified below. |
| 2 — Features and models | pass | `python3 src/train/train.py` completed reproducibly; all three leakage-safe candidate pipelines were evaluated with five-fold stratified CV and all four metrics, and `reports/model_comparison.md` records the comparison and champion rule. |
| 3 — Experiment tracking | pass | Three FINISHED local MLflow runs with required parameters, metrics, author tags, fitted pipelines, and EDA artifacts; champion registry version 1 is READY. Reloaded all three pipelines and verified predictions on 303 rows. |
| 4 — Packaging and reproducibility | not started | A fresh virtual environment can install, train, and run inference on a sample. |
| 5 — Tests and CI | not started | Local lint/tests pass; workflow contains lint, test, and train jobs. |
| 6 — Container | not started | Docker build/run and `/predict` smoke test succeed; request/response are recorded. |
| 7 — Kubernetes | not started | Minikube pod runs and the sample succeeds through the Service; command output and response are recorded. |
| 8 — Monitoring and logging | not started | A prediction creates a JSON log line and increments Prometheus request metrics. |
| 9 — Report pack | not started | Required report deliverables are complete and cross-checked. |

## Phase 0 evidence

- Baseline commands: `whoami`, `hostname`, `pwd`, `python3 --version`, `git --version`, `docker --version`, `kubectl version --client`, `minikube version`, `free -h`, and `df -h`.
- Python: `Python 3.12.9`; gate requires 3.10 or newer.
- Docker: CLI is installed and `docker info` reached the Engine server.
- Minikube: `v1.35.0` is installed; `minikube status` reports no profile exists yet.
- Kubernetes client: `kubectl version --client` exited 127 (`/bin/bash: line 1: kubectl: command not found`). This is recorded for the Kubernetes phase; it does not fail the Phase 0 gate.
- GitHub Actions: `curl` to `https://api.github.com/repos/bheemreddy1729/heart-disease-prediction/actions/workflows` returned HTTP 200. This verifies endpoint access only; workflow execution remains unverified until Phase 5.
- Repository: existing `origin` is `https://github.com/bheemreddy1729/heart-disease-prediction.git`; no git initialization or push was performed.
- No packages or tools were installed.

## Phase 0 review corrections

- Added author attribution to the baseline documents and normalized the Phase 0 state to `pass`.
- Corrected the memory description to distinguish total from available memory.
- Clarified that GitHub Actions endpoint access is not workflow execution evidence.
- Reviewed the committed VM evidence remotely; no VM commands were rerun during this documentation review.

## Phase 1 evidence

- Installed only the pinned Phase 1 dependencies from `requirements.txt` into the current user environment with `python3 -m pip install --user -r requirements.txt`.
- In the main VM checkout, `python3 src/data/download_heart.py`, `python3 src/data/prepare.py`, and `python3 src/eda/explore.py` succeeded and wrote the raw source, processed CSV, EDA summary, and three figures listed below.
- Verified source-aligned row count (303), 13 feature columns, target mapping (`0`: 164; `1`: 139), and preservation/reporting of six missing cells (`ca`: 4; `thal`: 2). All three PNGs are non-empty valid PNG files; the summary contains author attribution, missingness, and class counts.
- `python3 -m compileall -q src` and `git diff --check` succeeded.
- Missing feature values are retained in the processed file, not dropped or imputed; missing values are omitted per feature in histograms and pairwise in correlations. The decision and rationale are recorded in `docs/DECISIONS.md`.
- **Phase 1 review corrections:** Download, preparation, and EDA console status lines now each include `Author: 2025ae05142`; the downloader also writes that attribution into the generated `data/raw/README.md`.

### Separate-checkout regeneration

To avoid relying on the committed Phase 1 outputs, used a detached worktree at commit `7791642` at `/home/s2025ae05142/workspace/Assignment-I/heart-disease-phase1-repro`. Since the attribution corrections are uncommitted (and no commit was requested), copied the three corrected scripts from the main checkout into the detached worktree. Removed its raw and processed data, raw-data pointer, EDA summary, and three figures before running the following commands from that worktree:

```sh
cd /home/s2025ae05142/workspace/Assignment-I/heart-disease-phase1-repro
python3 src/data/download_heart.py
python3 src/data/prepare.py
python3 src/eda/explore.py
```

Results, in command order:

```text
Downloaded /home/s2025ae05142/workspace/Assignment-I/heart-disease-phase1-repro/data/raw/processed.cleveland.data (Author: 2025ae05142)
Wrote /home/s2025ae05142/workspace/Assignment-I/heart-disease-phase1-repro/data/processed/heart.csv (Author: 2025ae05142)
Wrote EDA figures to /home/s2025ae05142/workspace/Assignment-I/heart-disease-phase1-repro/reports/figures and summary to /home/s2025ae05142/workspace/Assignment-I/heart-disease-phase1-repro/reports/eda_summary.md (Author: 2025ae05142)
```

Verified that this checkout regenerated all seven non-empty outputs (raw source, attributed raw-data README, processed table, attributed summary, and three figures) from the cleared state. The regenerated table has 303 rows, target counts 164/139, and six retained missing values (`ca`: 4; `thal`: 2).

After regeneration, repeated the same three commands in the main checkout so its generated raw-data README uses the same attributed format. Compared SHA-256 hashes for all seven Phase 1 outputs between the main and detached checkouts; every file matched byte-for-byte. `git diff --check` and Python AST parsing of all three scripts passed.

## Phase 2 evidence

- Recorded classifier, preprocessing, validation, seed, champion-selection, rationale, alternatives, and scikit-learn documentation sources in the Phase 2 section of `docs/DECISIONS.md` before implementing the training script.
- Added `scikit-learn==1.9.1` to `requirements.txt`; installed the pinned requirements user-wide with `python3 -m pip install --user -r requirements.txt` on the VM. Runtime versions used: Python 3.12.9, pandas 2.3.3, scikit-learn 1.9.1, and SciPy 1.18.1.
- `python3 src/train/train.py` completed successfully from the repository root and wrote `reports/model_comparison.md`. After review correction, every console line includes the author tag; every model row carries `2025ae05142` in the `author=2025ae05142` column.
- The training module compares Logistic Regression, Random Forest, and RBF SVC. Its preprocessing is part of each scikit-learn `Pipeline`: numeric median imputation and scaling, categorical most-frequent imputation and one-hot encoding. `cross_validate` evaluates the full pipeline inside each fold, so preprocessing statistics and categories are learned only from that fold's training partition.
- Validation: five-fold `StratifiedKFold(shuffle=True, random_state=42)`, reporting mean and sample standard deviation for accuracy, precision, recall, and ROC-AUC.
- Champion rule: highest mean recall, then ROC-AUC, then precision; accuracy is reported but is not the selection criterion. The resulting champion is `rbf_svc`.
- Regenerated results (mean ± sample standard deviation; four decimal places):

  | Model | Accuracy | Precision | Recall | ROC-AUC |
  |---|---:|---:|---:|---:|
  | logistic_regression | 0.8547 ± 0.0542 | 0.8744 ± 0.0640 | 0.7979 ± 0.0812 | 0.9188 ± 0.0232 |
  | random_forest | 0.8384 ± 0.0310 | 0.8505 ± 0.0612 | 0.7913 ± 0.0306 | 0.9144 ± 0.0255 |
  | rbf_svc | 0.8448 ± 0.0506 | 0.8501 ± 0.0666 | 0.8056 ± 0.0656 | 0.9021 ± 0.0319 |
- Re-ran `python3 src/train/train.py`; `sha256sum --check /tmp/phase2-review-model-report-final.sha256` confirmed the generated report was byte-for-byte identical on rerun. The report and progress table both show the Random Forest ROC-AUC as `0.9144 ± 0.0255`.
- Separately verified all three fitted pipelines predict three rows, every metric mean is within [0, 1], standard deviations are nonnegative, all four metrics and all candidates appear in the report, and its author header is present.
- `git diff --check` passed.
- **Phase 2 review corrections:** Regenerated metrics confirm Random Forest ROC-AUC is `0.9144 ± 0.0255`; the report and progress table now use four decimal places and agree. Training console output now has an `author=2025ae05142` column on every model row; its header, champion line, and report-path line also include the author. Checked every emitted console line.
- **Confidence plan before artifact packaging:** The Phase 2 decisions document specifies wrapping the complete preprocessing-plus-RBF-SVC pipeline in sigmoid `CalibratedClassifierCV` with five shuffled stratified folds (`random_state=42`, `ensemble=True`), returning the winning class's averaged calibrated probability as `confidence`, and checking Brier score/reliability before calling it calibrated. No confidence-bearing artifact has been packaged in this phase.

## Phase 3 evidence

Author: `2025ae05142`

Execution location: Prayogshala Linux VM, user `s2025ae05142`, repository `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`, Python 3.12.9.

- Probed MLflow availability (not installed), then added `mlflow==3.17.1` and ran `python3 -m pip install --user -r requirements.txt` successfully. Pip warned that user-level CLI scripts are not on `PATH`; the Python APIs used below work without a PATH change.
- Recorded tracking, artifact, registry, and serialization choices in `docs/DECISIONS.md`. The training command now tracks each candidate in local SQLite `mlflow.db`, with file artifacts under `mlruns/`; both are gitignored, along with SQLite sidecars. MLflow telemetry is disabled before import in the training flow.
- `python3 src/train/train.py` successfully logged the three candidates and registered `rbf_svc` as `heart-disease-champion-2025ae05142`, version `1`. Generated `reports/mlflow_summary.md` contains real run IDs and model URIs from this VM.
- Verified each FINISHED run's author/model/champion tags, data SHA-256, estimator/preprocessing parameters, CV seed and fold count, all four metric means and sample standard deviations, three EDA figures, comparison report, model signature, and fitted full pipeline. Reloaded every logged model and the registered champion through MLflow; predictions were valid binary labels for all 303 rows. Logged metrics match the generated Phase 2 comparison exactly.
- `git diff --exit-code -- reports/model_comparison.md` passed: tracking did not alter Phase 2 CV results.
- `git check-ignore mlflow.db mlflow.db-wal mlruns/` confirmed runtime storage is excluded. `git ls-files mlflow.db mlruns` returned no tracked runtime files. `git diff --check` passed and editor diagnostics found no Python errors.
- **Phase 3 review correction:** The generated summary now interpolates `len(data)` rather than hardcoding 303 rows. On the VM, evaluated the actual summary expression extracted from the training module's AST with 17-row and 303-row inputs; both returned the correct row count. `git diff --check` passed. This targeted check did not retrain models or create new MLflow runs/registry versions; the existing 303-row summary remains accurate.

### Failures retained and resolved

1. First tracking attempt raised `TypeError: Object of type ColumnTransformer is not JSON serializable` while logging nested parameters. Fixed by storing sklearn parameter representations as strings; failed run `aedaaf53749645348e8fd8d1b771478f` remains visible.
2. Next attempt raised `UntrustedTypesFoundException` for `numpy.dtype` using MLflow 3.17.1's default skops serializer. Explicit cloudpickle serialization resolved this compatibility issue; failed run `84497ea7fb344de58b1116ac4879da06` remains visible. MLflow's warning about loading only trusted pickle-based artifacts is retained, not suppressed.

### Exact gate listing command and output

Ran from the repository root:

```sh
MLFLOW_DISABLE_TELEMETRY=true MLFLOW_DISABLE_AGENT_HINT=true python3 - <<'PY'
from pathlib import Path
from mlflow import MlflowClient
uri = f"sqlite:///{Path.cwd() / 'mlflow.db'}"
client = MlflowClient(tracking_uri=uri, registry_uri=uri)
experiment = client.get_experiment_by_name('heart-disease-2025ae05142')
for run in client.search_runs([experiment.experiment_id], order_by=['start_time ASC']):
    print('Author: 2025ae05142', run.data.tags['model'], run.info.status, run.info.run_id)
for version in client.search_model_versions("name = 'heart-disease-champion-2025ae05142'"):
    print('Author: 2025ae05142 registry', version.version, version.status, version.run_id)
PY
```

```text
Author: 2025ae05142 logistic_regression FAILED aedaaf53749645348e8fd8d1b771478f
Author: 2025ae05142 logistic_regression FAILED 84497ea7fb344de58b1116ac4879da06
Author: 2025ae05142 logistic_regression FINISHED 36f54d74d4604552aaeec49ca8e4dd5c
Author: 2025ae05142 random_forest FINISHED f1fd9806c995443db667aee24e95dd87
Author: 2025ae05142 rbf_svc FINISHED b31ee47545d04752a9bd7f9b9f7b1b9c
Author: 2025ae05142 registry 1 READY b31ee47545d04752a9bd7f9b9f7b1b9c
```

The Phase 3 champion remains the uncalibrated Phase 2 pipeline. Probability calibration and confidence validation are documented plans for Phase 4, not completed work. No serving, packaging, commit, or push was performed.

**Next:** Review Phase 3, then send `start phase 4`.
