# Assignment progress

Author: `2025ae05142`

Complete one phase at a time. A phase is complete only when its gate is met; record blockers and evidence here.

| Phase | Status | Gate / evidence |
|---|---|---|
| 0 — Lab baseline | pass | `docs/ENVIRONMENT.md` records the Linux VM baseline. Python 3.12.9 satisfies the >=3.10 gate; Docker and Minikube are installed. GitHub Actions API access returned HTTP 200; workflow execution remains unverified until Phase 5. |
| 1 — Data and EDA | pass | UCI download, preparation, and EDA commands succeeded; 303 rows, target counts 164/139, 6 reported missing feature values, summary, and all three figures verified below. |
| 2 — Features and models | pass | `python3 src/train/train.py` completed reproducibly; all three leakage-safe candidate pipelines were evaluated with five-fold stratified CV and all four metrics, and `reports/model_comparison.md` records the comparison and champion rule. |
| 3 — Experiment tracking | pass | Three FINISHED local MLflow runs with required parameters, metrics, author tags, fitted pipelines, and EDA artifacts; champion registry version 1 is READY. Reloaded all three pipelines and verified predictions on 303 rows. |
| 4 — Packaging and reproducibility | pass | Fresh isolated `.venv-phase4` installed pinned requirements, regenerated data/EDA, trained, packaged the full calibrated pipeline, and produced the sample JSON below. Repackaging reproduced artifact/report hashes. |
| 5 — Tests and CI | pass | Ruff and 51 pytest cases pass locally; hosted run `38787031961` passed lint, test, and train with uploaded evidence. Dedicated branch run `38789263010` failed on an intentional test; reverting that commit restored green CI in run `38789471935`. Screenshots and run links recorded below. |
| 6 — Container | pass | Inference-only Docker image built and ran on the VM as a non-root user; `GET /health` returned `{"status":"ok"}`, and real sample `POST /predict` returned expected JSON. Dedicated request/response and build/run evidence is in `docs/docker_smoke.md`. Ruff and all 55 pytest cases passed. |
| 7 — Kubernetes | pass | Assignment rubric met: NodePort Service, deployment access note in `docs/DEPLOY.md`, kubectl output and sample curl response in `docs/deploy_smoke.md`; pod 1/1 Running and the sample succeeds through Minikube's NodePort URL. |
| 8 — Monitoring and logging | in progress | Monitoring gate and review fixes verified locally and on Minikube. Waiting for a fresh hosted Actions run of the corrected revision; changes are not committed/pushed. |
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

### Phase 3 UI screenshots

Author: `2025ae05142`

At the student's explicit request, captured and visually checked the live MLflow UI on the VM using its installed Firefox 128 ESR in headless mode. The integrated browser's forwarded port required GitHub sign-in, so screenshots were taken directly from localhost instead; no public port access was enabled and no extra browser packages were installed.

Started the temporary UI with:

```sh
MLFLOW_DISABLE_TELEMETRY=true MLFLOW_DISABLE_AGENT_HINT=true python3 -m mlflow server --backend-store-uri sqlite:////home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction/mlflow.db --default-artifact-root file:///home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction/mlruns --host 127.0.0.1 --port 5000 --workers 1
```

`curl --fail http://127.0.0.1:5000/health` returned `OK`. Captured rendered UI screenshots at 2200 x 1100 after confirming the expected content had loaded:

- [Experiment runs](../screenshots/phase-3-mlflow-experiment.png): three successful runs, two retained failures, four mean metrics, and author tags.
- [Champion run](../screenshots/phase-3-mlflow-champion-run.png): metrics, preprocessing parameters, FINISHED status, run ID, champion/author tags, and registry link.
- [Logged EDA artifacts](../screenshots/phase-3-mlflow-artifacts.png): the three EDA figure files with the logged class-balance image preview.
- [Registered champion](../screenshots/phase-3-mlflow-registry.png): version 1, source run/model, author tag, uncalibrated status, and input/output schema.

These are actual MLflow UI captures, not recreated charts or mockups. No training, new experiment runs, or new registry versions were needed. Stopped the temporary UI and isolated Firefox processes after capture. Phase 4 remains not started.

## Phase 4 evidence

Author: `2025ae05142`

Execution location: Prayogshala Linux VM, user `s2025ae05142`, repository `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`, Python 3.12.9.

### Fresh-environment gate

Probed available dependencies, disk, and memory before installation. `.venv-phase4` did not exist; created it without system-site-packages. Verified `sys.prefix != sys.base_prefix`, `include-system-site-packages = false`, and no user-site `.local` packages on `sys.path`. The install completed successfully (slow package writes on the workspace filesystem); `pip check` returned `No broken requirements found.` No validation commands failed in this phase.

Ran the exact reproduction sequence from the repository root:

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

The final command returned:

```json
[{"prediction": 0, "confidence": 0.7466949562461239}]
```

This is the probability of the returned absent-disease class for the documented sample, not an independent test or clinical assurance. Labels use maximum calibrated class probability and can differ from the original SVC's label decision.

### Packaged artifact and evaluation

- `src/train/package.py` recomputes the established three-candidate CV comparison and champion rule, selecting `rbf_svc`. It evaluates a sigmoid calibrator around the entire preprocessing/classifier pipeline using five outer stratified validation folds and five inner calibration folds, shuffle and seed 42, with `ensemble=True`.
- Only after out-of-fold evaluation, fit the final pipeline on all 303 rows and write `models/heart_pipeline.joblib` plus `models/heart_pipeline.json` provenance. Each of its five fitted calibration estimators contains the full imputation/scaling/encoding/classifier pipeline. The binary and virtual environment are gitignored but exist persistently on this VM.
- `reports/calibration_summary.md` and `reports/figures/calibration_reliability.png` record separate pooled out-of-fold metrics and visually inspected reliability/bin-count diagnostics:

  | Metric | Value |
  |---|---:|
  | Accuracy | 0.854785 |
  | Precision | 0.851852 |
  | Recall | 0.827338 |
  | ROC-AUC | 0.905115 |
  | Brier score | 0.121745 |
  | Log loss | 0.392889 |
  | Training-fold prevalence baseline Brier score | 0.248313 |

- These are post-selection diagnostics: the candidate was selected using this same dataset. No claim of unbiased final-test performance, clinical suitability, or perfect calibration is made. The original Phase 2 comparison remains unchanged.
- Re-ran `.venv-phase4/bin/python -m src.train.package`; SHA-256 comparison confirmed the model binary and calibration summary were byte-for-byte identical. Sample JSON was identical on repeated prediction and after repackaging. Artifact SHA-256: `e9e7aee665648300c2eac5a917cca89a2c401f9c32a881a65e5c20df99d0fc4c`.
- Fresh-environment candidate training appended successful MLflow runs `e31403f4bb7d4506b39ceb1ff05004c4` (Logistic Regression), `278a020c22ae4530aabafb6bd5fc1307` (Random Forest), and `5ad5e00bd4714b998beb1b868379a2b2` (RBF SVC). The uncalibrated registry champion now also has version 2; version 1 and the Phase 3 screenshots remain historical evidence. The regenerated MLflow summary lists the latest batch. The calibrated local serving artifact is deliberately separate and has not been registered under the uncalibrated model's metrics.

### Inference and validation

- Added `src/infer/predict.py` with `predict_records(records)`, returning only `prediction` and `confidence` keys. Loads the trusted local full pipeline, never refits or accesses MLflow. README includes exact setup, data, training, packaging, and sample-inference commands plus trust and statistical limitations.
- Live assertions in the fresh environment verified deterministic single/batch predictions, null-value imputation, nine invalid-input cases (empty/wrong container, non-record, extra/missing keys, string, boolean, NaN, infinity), missing-artifact errors, rejection of non-pipeline artifacts and malformed probabilities, provenance hashes, five complete fitted inner pipelines, and JSON output shape/range.
- Subprocess checks verified successful stdout is parseable JSON, and invalid CLI input exits 1 with no success output and `Author: 2025ae05142 Inference failed:` on stderr.
- `git diff --exit-code -- reports/model_comparison.md` confirmed original model-comparison evidence is unchanged. `git check-ignore .venv-phase4/ models/heart_pipeline.joblib` confirmed runtime exclusions. Editor diagnostics and `git diff --check` passed.
- No CI/tests infrastructure, serving API, containers, or deployment was started; no commit or push was made. Existing Phase 3 screenshot changes were preserved.

### Phase 4 documentation review follow-ups

- Documented the existing inference threshold in README, decisions, and the calibration report/generator: predict 1 when P(disease) > 0.5; otherwise 0. Exact ties return class 0 with confidence 0.5 because argmax selects the first class in `[0, 1]`.
- Updated the MLflow summary generator and existing summary to distinguish the uncalibrated registry candidate from the separate calibrated serving-artifact workflow. Training does not run packaging or verify its outputs; the text makes no claim that packaging has executed or that an existing artifact matches a new training run.
- On the VM, used `.venv-phase4/bin/python -B` assertions against the actual `predict_records` function with mocked probabilities 0.49, 0.50, and 0.51; verified predictions 0, 0, and 1, with the corresponding predicted-class confidence. Extracted the actual generator text with Python AST and confirmed it matches both saved reports. `git diff --check` passed.
- These are documentation/output-text corrections only; no retraining, repackaging, new MLflow runs, or registry versions were needed. Existing sample results and artifact hashes are unchanged; Phase 5 remains not started.

### Phase 4 screenshot evidence

Author: `2025ae05142`

- At the student's request, reran `.venv-phase4/bin/python -m src.train.package` and `.venv-phase4/bin/python -m src.infer.predict --input examples/patient.json` in an actual VM terminal. Both exited successfully; the sample again returned `[{"prediction": 0, "confidence": 0.7466949562461239}]`.
- Saved and visually checked the [packaging and inference screenshot](../screenshots/phase-4-packaging-inference.png). It shows the author tag, VM username, Python version, commands, packaging output, nested OOF metrics, and JSON prediction. Captured only the evidence terminal, not unrelated desktop windows.
- This reran local calibrated packaging, not MLflow training or registration. Closed the temporary capture terminal afterward. Phase 5 remains not started.

## Phase 5 evidence

Author: `2025ae05142`

### Implementation and local gate

- Probed the VM before installation: user `s2025ae05142`, HOME `/home/s2025ae05142`, Python 3.12.9. Neither pytest nor ruff was installed in `.venv-phase4`. Added `requirements-dev.txt` including the runtime manifest and pinned `pytest==8.4.2` and `ruff==0.14.0`, then installed into that isolated environment; no system installation.
- Added correctness-focused ruff and pytest configuration in `pyproject.toml`; excluded their runtime caches from git.
- Added 51 tests covering source schema/class counts/missingness, target binarization and invalid values, preparation round-trip, downloader validation/attribution with local response fixtures, real three-candidate evaluation, sample standard deviations, champion priorities/ties, fitted preprocessing isolation and unknown categories, invalid training data, real calibration packaging/provenance/hashes, and inference success/error/threshold/CLI behavior.
- Successful tests build their own real calibrated model in pytest temporary directories. They never rely on the ignored serving artifact or existing MLflow state, do not download data, and do not write the repository's reports or models.

Exact local validation commands:

```sh
.venv-phase4/bin/python -m pip install -r requirements-dev.txt
.venv-phase4/bin/python -m pip check
.venv-phase4/bin/python -m ruff check .
.venv-phase4/bin/python -m pytest -q
```

Results: `No broken requirements found.`, `All checks passed!`, and **51 passed in 15.08s**. The initial lint check caught one unused import in a new test fixture; removed it and reran successfully. The editor test runner reported `No tests found in the files`, so the authoritative run used the pinned environment's pytest CLI. Editor diagnostics for the workflow/configuration were clear.

### Isolated CI-command reproduction

- Added `.github/workflows/ci.yml` with Python 3.12 `lint`, `test`, and `train` jobs. Train requires both checks; all jobs have timeouts and read-only repository permissions. The train job uses the committed UCI raw snapshot (avoiding a live-source outage), regenerates processed data/EDA, logs actual MLflow runs, packages calibration, verifies JSON/provenance and registry reload, and uploads seven-day evidence. No deployment or commit/push step.
- Parsed the workflow with the existing PyYAML dependency using `BaseLoader` (preserving the `on` key), checked triggers/job dependencies, and compiled its embedded verification Python. This is a local structure check, not a hosted Actions run or complete Actions-service validation.
- Ran the following verification driver on the VM:

```sh
.venv-phase4/bin/python -u /home/s2025ae05142/.copilot/session-state/efa990de-681a-4eca-b022-e37b78971d1e/files/verify_phase5.py
```

The driver used `git archive HEAD` extracted into an isolated temporary checkout, overlaid only the new Phase 5 tests/manifests/workflow and cache exclusions, and asserted that `models/`, `mlflow.db`, and `mlruns/` were absent. It reused the pinned `.venv-phase4` interpreter (this is not a second fresh dependency installation), then executed the workflow's actual `run` blocks in job order, except dependency-install blocks already satisfied by that environment.

The train job's exact reproduction commands were:

```sh
python src/data/prepare.py
python src/eda/explore.py
python src/train/train.py
python -m src.train.package
python -m src.infer.predict --input examples/patient.json > prediction.json
```

Results in the isolated checkout:

- Ruff: `All checks passed!`; pytest: **51 passed in 15.78s**.
- Regenerated processed data and EDA; selected `rbf_svc` with unchanged CV metrics.
- Created three FINISHED runs in a fresh local SQLite store: Logistic Regression `490c66492c584167a8a182383d551467`, Random Forest `b67aa6232b774efab7b304a0aa1731c7`, RBF SVC `ff0581f3caa0433fad66bdb48d57f3df`. Registered uncalibrated champion version 1 in this separate store, not the main checkout's registry.
- Workflow assertions verified all three run author/confidence/data-hash tags and four metrics/stds, READY registry version linked to the champion, and full registered pipeline reload/prediction for all 303 rows.
- Packaging and sample CLI succeeded; JSON was `[{"prediction": 0, "confidence": 0.7466949562461239}]`. Workflow assertions verified exact prediction keys/types/ranges and provenance hashes. Main-checkout models, reports, and MLflow history were not overwritten by this reproduction.
- The driver and captured transcript are retained in session evidence; the isolated scratch checkout is removed after validation. These commands validate job behavior locally, not runner provisioning, dependency installation on GitHub, action execution, or artifact upload.

### Hosted CI status and phase boundary

- GitHub Actions API `list_workflows` for `bheemreddy1729/heart-disease-prediction` returned `{"total_count": 0}` before publication. Actions is reachable, but there is no published workflow or hosted green run to inspect yet. No claim of hosted CI success or artifact upload is made.
- Local Phase 5 gate is met. Hosted evidence remains pending explicit student authorization to publish and run the workflow. No commit, push, dispatch, serving API, Docker phase, or deployment was performed.

**Next:** Review Phase 5 and authorize workflow publication/execution when ready. Stop before Phase 6.

### Phase 5 screenshot capture and publication attempt

Author: `2025ae05142`

- Student explicitly authorized committing/pushing Phase 5 and running CI to capture all three screenshots.
- Captured and visually checked [local validation](../screenshots/phase-5-local-validation.png) from an actual VM terminal: Python 3.12.9, `pip check` successful, ruff successful, and **51 passed in 16.72s**. Cropped unrelated desktop chrome; no output was recreated.
- Created local commit `9988eba` containing Phase 5 implementation and the local screenshot. Initial `git push origin main` failed with `fatal: could not read Username for 'https://github.com': terminal prompts disabled`. Configured the existing authenticated GitHub CLI credential helper using `gh auth setup-git` and retried.
- The authenticated `git push origin main` was rejected: `refusing to allow an OAuth App to create or update workflow .github/workflows/ci.yml without workflow scope`. No remote changes or hosted workflow run occurred. Hosted run/training-evidence screenshots remain blocked until the student grants workflow scope or publishes this commit through an appropriately authorized client. Stopped publication attempts rather than bypassing the permission restriction.

### Phase 5 hosted success and remaining screenshots

Author: `2025ae05142`

- After the student resolved publication permissions, confirmed commit `7589a6380175873c3f8eed0a009f502a9e559f10` was published on `main`. Its actual push-triggered [Actions run 38787031961](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38787031961) completed with **success**: lint, test, and train all green; total duration 2m 22s.
- Retrieved the actual hosted train-job log with `gh run view 38787031961 --job 116602044720 --log`. It confirms packaged-artifact/sample prediction verification, three MLflow runs and registry reload, and successful upload of `training-evidence-2025ae05142` (1,531,644 bytes; artifact ID `11997744157`). Sample confidence remained `0.7466949562461239`.
- Saved and visually checked actual GitHub UI captures: [green hosted run](../screenshots/phase-5-actions-run.png) and [uploaded training evidence](../screenshots/phase-5-training-evidence.png). Together with [local validation](../screenshots/phase-5-local-validation.png), all three requested Phase 5 screenshots now exist. No mocked or recreated CI UI was used.
- GitHub displayed non-failing Node.js action-runtime deprecation warnings and an upcoming `ubuntu-latest` migration notice. These did not prevent any job or artifact upload from succeeding.
- Closed the temporary isolated Firefox capture process. Phase 5's hosted gate is now met; the earlier pending/permission entries above are historical. No Phase 6 work was started.

### Phase 5 review correction: deliberate failure followed by revert

Author: `2025ae05142`

The reviewer correctly identified that successful runs alone did not demonstrate CI catching a deliberately failing test. The earlier completion statement omitted this requirement; the demonstration below now supplies it.

- With explicit student authorization, created branch `phase5/failed-test-demo` in an isolated worktree from main commit `c87fdbb`. Main's branch pointer and application/test code were left unchanged; the intentional failure was never merged.
- Committed `b9a445cae417a588b1c1a1824d1ae0831f0fb236`, adding only `tests/test_ci_failure_demo.py` with `test_intentional_ci_failure_2025ae05142` and an unconditional assertion carrying author attribution.
- Pushed that branch and waited for actual [failed run 38789263010](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38789263010). Lint passed, test failed, and dependent training was skipped. Retrieved `gh run view 38789263010 --log-failed` and verified the cause was the deliberate assertion, not infrastructure: **1 failed, 51 passed in 7.47s**, with `AssertionError: Author: 2025ae05142 Deliberate CI failure; revert this demo commit.`
- Only after confirming that failure, ran `git revert --no-edit b9a445cae417a588b1c1a1824d1ae0831f0fb236`, creating revert commit `3b17b0cc4a0a5670b13003e7b8c67b76376d44c9`, and pushed the same branch again. No force push or history rewrite.
- Verified `git diff --exit-code c87fdbb HEAD` in the demo worktree: no differences after the revert. The failing test no longer exists at the branch tip.
- Actual [recovered run 38789471935](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38789471935) passed lint, test, and train, with **51 passed in 8.88s** and an uploaded training artifact. Total duration: 2m 36s.
- Saved and visually checked actual GitHub UI screenshots: [deliberately failed CI](../screenshots/phase-5-deliberate-failure.png) and [green CI after revert](../screenshots/phase-5-reverted-success.png). These show the same demo branch and the distinct failure/revert commits.
- Retained the remote demo branch and both commits/runs as reviewable evidence; removed only its temporary local worktree and stopped its temporary Firefox process. This progress update and screenshots are saved locally for review; no new commit to main was made. Phase 6 remains not started.

## Phase 6 evidence

Author: `2025ae05142`

- **Design:** Added FastAPI `GET /health` and `POST /predict`, with prediction validation reused from `predict_records`, and an inference-only Python 3.12 slim image. Exact artifact dependency versions and pinned FastAPI/Uvicorn versions are in `requirements-serving.txt`; the image copies the locally generated packaged model and source, installs no training/MLflow/EDA stack, and runs as UID 10001. The decision and alternatives are recorded in `docs/DECISIONS.md`.
- **VM:** Ran as user `s2025ae05142` with `HOME=/home/s2025ae05142` from `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`; Docker Engine 28.0.1 was reachable.
- **Dependency and tests:** `.venv-phase4/bin/python -m pip install -r requirements-dev.txt` succeeded. `.venv-phase4/bin/python -m ruff check . && .venv-phase4/bin/python -m pytest -q` succeeded: **54 passed in 17.11s**, with one non-failing Starlette/AnyIO deprecation warning.
- **Build:** `docker build --tag heart-disease-2025ae05142:phase6 .` succeeded. The local image is 469,189,807 bytes. The build context was 272.33 kB.
- **Run and smoke test:** Started with `docker run --detach --name heart-disease-phase6 --publish 127.0.0.1:8000:8000 heart-disease-2025ae05142:phase6`. `docker exec heart-disease-phase6 id` confirmed `uid=10001(app)`. Posting `examples/patient.json` with `curl --fail-with-body --silent --show-error --retry 30 --retry-delay 1 --retry-connrefused -H 'Content-Type: application/json' --data-binary @examples/patient.json http://127.0.0.1:8000/predict` returned `[{"prediction":0,"confidence":0.7466949562461239}]`; posting `[]` returned HTTP 422 with an explanatory validation message. Container logs confirmed Uvicorn startup and `POST /predict` 200.
- **Failures:** No Phase 6 gate failures. The test run emitted the noted third-party deprecation warning only; the workflow remains Phase 5 evidence and was not re-run.

**Next:** Review Phase 6 and authorize Phase 7 when ready. Stop before Kubernetes.

### Phase 6 review corrections

Author: `2025ae05142`

- Added `GET /health`; `.venv-phase4/bin/python -m ruff check . && .venv-phase4/bin/python -m pytest -q` passed with **55 passed in 15.85s** and one non-failing third-party deprecation warning.
- Confirmed `models/heart_pipeline.joblib` exists locally, is ignored by `.gitignore`, and is not tracked. It is a locally generated packaged artifact required before Docker build; it is not checked in.
- Rebuilt with `docker build --tag heart-disease-2025ae05142:phase6 .` and ran on the VM. Live `curl` to `/health` returned `{"status":"ok"}`; sample `/predict` returned `[{"prediction":0,"confidence":0.7466949562461239}]`; `docker exec ... id` confirmed UID 10001 (`app`).
- Added [dedicated Docker smoke evidence](docker_smoke.md) containing the request body, response, VM execution location, build/run commands, and non-root verification. The temporary review container was stopped and removed.
- Captured actual VM terminal screenshots while the container was live: [health endpoint and non-root verification](../screenshots/phase-6-health.png) and [sample request body and prediction response](../screenshots/phase-6-predict.png). Both show real commands and responses; neither was recreated.
- Captured additional actual Docker CLI evidence for [the built image](../screenshots/phase-6-docker-image.png) and [running container usage](../screenshots/phase-6-docker-container.png), including image ID/size, live status, published loopback port, CPU/memory stats, non-root user, and health response.
- Corrected the earlier phrase “checked-in packaged model”: the model is gitignored and untracked, and the source artifact is locally generated before image build. No model binary was added to git.

Phase 6 remains complete. Stop before Kubernetes until student review.

## Phase 7 validation (initial; superseded by rubric correction below)

Author: `2025ae05142`

- **VM:** User `s2025ae05142`, home `/home/s2025ae05142`, repository `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`, Docker Engine 28.0.1, Minikube 1.35.0. Standalone `kubectl` is not installed; the Minikube-bundled client v1.32.0 was available and the Kubernetes server reports v1.32.0.
- **Cluster:** `minikube start -p heart-disease --driver=docker --cpus=2 --memory=4096 --disk-size=20g` succeeded. `minikube status -p heart-disease` reported host, kubelet, and API server running.
- **Image:** `minikube image load --profile=heart-disease heart-disease-2025ae05142:phase6` succeeded. The pod used local image ID `sha256:b6ef0aa7a8454109bdb78c96b3fc91aef71a7ccd559f85189d311305d831105f`; image pull policy is `Never`.
- **Deployment:** `minikube kubectl -p heart-disease -- apply -f k8s/namespace.yaml` and `minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/service.yaml` succeeded. `minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api -n heart-disease --timeout=180s` returned `deployment "heart-disease-api" successfully rolled out`.
- **Workload status before rubric correction:** Pod `heart-disease-api-745b445899-b5rgd` was `1/1 Running`, `ready=true`, `restarts=0`; the initial ClusterIP Service had endpoint `10.244.0.3:8000`. Probes use `/health`; pod security context runs UID 10001 with a read-only root filesystem and resource requests/limits.
- **Initial Service test:** The first implementation used ClusterIP and loopback port-forward; it proved pod and Service connectivity but did not meet the assignment's required NodePort/LoadBalancer type. These results are retained as historical validation only; final gate depends on the NodePort correction and `minikube service` verification below.
- **Initial screenshot:** The first screenshot showed the ClusterIP implementation and is superseded by the NodePort recapture linked in final evidence below.
- **Failure note:** An initial client version probe using unsupported `minikube kubectl -p heart-disease -- version --short` exited 1 with `unknown flag: --short`. Corrected it to `minikube kubectl -p heart-disease -- version --output=yaml`, which returned client and server v1.32.0. This did not affect cluster creation or the deployment gate.
- The initial loopback port-forward was stopped. The ClusterIP implementation did not satisfy the rubric; final evidence below records the corrected NodePort design. No monitoring work was started.

### Phase 7 rubric evidence correction

Author: `2025ae05142`

- Rubric requirement found on recheck in `.github/agents/mlops-assignment.agent.md`: Service must be `LoadBalancer` or `NodePort`; `docs/DEPLOY.md` must describe endpoint access; and `docs/deploy_smoke.md` must retain kubectl output and curl result.
- Updated `k8s/service.yaml` to `NodePort` at `30080`, with no public cloud dependency. Updated the Phase 7 design decision to match the rubric.
- Final validation is recorded below after the updated NodePort was applied and the sample prediction succeeded at the URL returned by `minikube service`.

#### Final NodePort gate

- Applied `k8s/service.yaml`; `minikube kubectl -p heart-disease -- get service heart-disease-api -n heart-disease -o wide` returned `TYPE=NodePort`, `PORT(S)=80:30080/TCP`. Deployment stayed 1/1 available and its ready pod had zero restarts.
- The exact endpoint-access note is in `docs/DEPLOY.md`; the dedicated required `docs/deploy_smoke.md` records the kubectl output and curl request/response.
- `minikube service heart-disease-api -p heart-disease -n heart-disease --url` returned `http://192.168.49.2:30080`. `curl --fail-with-body --silent --show-error http://192.168.49.2:30080/health` returned `{"status":"ok"}`; posting `examples/patient.json` to `http://192.168.49.2:30080/predict` returned `[{"prediction":0,"confidence":0.7466949562461239}]`.
- Recaptured actual VM terminal evidence after the service-type correction: [NodePort workload and live prediction](../screenshots/phase-7-kubernetes.png). The previous ClusterIP screenshot is replaced.
- Phase 7 gate is met. Minikube and the deployment remain running; no Phase 8 monitoring work has started.

## Phase 8 evidence

- **Execution location:** BITS Prayogshala Linux VM, user `s2025ae05142`; Minikube profile `heart-disease`. The API image `heart-disease-2025ae05142:phase8` built successfully, loaded into Minikube, and rolled out. Prometheus `v2.55.1` and Grafana `11.4.0` were deployed from the pinned official images.
- **Workloads:** `minikube kubectl -p heart-disease -- get pods,svc -n heart-disease -o wide` showed API, Prometheus, and Grafana each `1/1 Running`, zero restarts. API remains on NodePort `30080`; monitoring Services are ClusterIP.
- **HTTP/API validation:** The live NodePort returned `{"status":"ok"}` from `GET /health` and `[{ "prediction": 0, "confidence": 0.7466949562461239 }]` (without spaces in the actual JSON) from `POST /predict` using `examples/patient.json`. Five further valid requests returned HTTP 200; an invalid `{}` returned HTTP 422.
- **Logs and metrics:** `minikube kubectl -p heart-disease -- logs deployment/heart-disease-api -n heart-disease --since=30m` contained seven JSON events for seven requests: six successful and one validation failure. Each event had author `2025ae05142`, timestamp, feature names only, prediction, confidence, and latency; the failed request logged null prediction/confidence. The API's live metrics reported request counter and histogram count `7`. An observed request increased the counter from `0` to `1`.
- **Prometheus/Grafana:** Prometheus target `heart-disease-api.heart-disease.svc.cluster.local:80` reported `health: up` with no scrape error; querying `heart_disease_prediction_requests_total` returned `7`. Grafana `/api/health` reported database `ok`, version `11.4.0`; dashboard `heart-disease-api` loaded with request-rate, latency-percentile, and total-request panels. The [live Grafana dashboard screenshot](../screenshots/phase-8-grafana-dashboard.png) shows count `7`.
- **Resource gate:** `free -h` reported 15 GiB total and 9.8 GiB available. The Minikube node has 4 CPUs and 15,968,384 KiB memory; all scheduled workload requests total 1,050m CPU/938Mi and limits total 3 CPUs/2,730Mi. Prometheus and Grafana each request 100m CPU/256Mi and are limited to 1 CPU/768Mi. The `kubectl top` Metrics API was unavailable; node capacity and scheduled requests were verified with `free -h` and `minikube kubectl -p heart-disease -- describe node heart-disease`.
- **Validation:** On the VM, `.venv-phase4/bin/python -m ruff check .` passed; `.venv-phase4/bin/python -m pytest -q` reported `57 passed` (one non-failing Starlette/AnyIO deprecation warning); `.venv-phase4/bin/python -m pip check` reported no broken requirements. The dashboard JSON parses with `python3 -m json.tool`, and `git diff --check` passed.
- **Resolved transient:** A controlled Grafana rollout restart terminated the existing port-forward, and the first screenshot attempt caught the loading state. The port-forward was re-established after rollout; Grafana health, dashboard provisioning, all rendered panels, and the final screenshot were then verified. No Phase 9 work has started.

### Phase 8 review correction

- The hosted run for Phase 8 commit `7e6934b0f9c632d9bd5040bf3844050b06315d1a` (`38952933435`) passed lint but failed its test job: 1 failed, 56 passed; training was skipped. The privacy-log test attempted to load the ignored `models/heart_pipeline.joblib`, absent on the clean runner.
- Updated that test to point inference at the existing `packaged` temporary-fixture artifact. No checked-in or prior-training artifact is needed.
- Moved request logging, counter increments, and latency observations from the endpoint into ASGI middleware scoped to `POST /predict`. Middleware records successful predictions as before and also records malformed JSON/missing-body 422 responses, with empty feature names and null prediction/confidence. The valid-request test asserts each counter and histogram increments exactly once.
- `.venv-phase4/bin/python -m pytest -q tests/test_api.py`: `8 passed`. The full `.venv-phase4/bin/python -m pytest -q` run passed `59` tests while the ignored `models/heart_pipeline.joblib` file was temporarily moved away, then restored. Ruff check/format, `pip check`, and `git diff --check` passed.
- Built and deployed `heart-disease-2025ae05142:phase8-review`; all three API/Prometheus/Grafana pods were ready, API with zero restarts. Live VM calls returned HTTP 200 for the sample, HTTP 422 for malformed JSON, and HTTP 422 for a missing body. Counter and histogram each increased from `0` to `3`, and pod logs contained exactly three events: one prediction and two invalid-body events with no feature values. Prometheus then reported target `up`, no scrape error, and request counter `3`.
- The only hosted run on the current published Phase 8 revision is run [`38952933435`](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38952933435): lint passed; tests failed `1 failed, 56 passed` for the clean-runner missing model; training was skipped. No hosted run can yet verify these local corrections because they are uncommitted/unpushed. Per project rules, no commit or push was made; Phase 8 remains `in progress` pending explicit publication permission and a green hosted run.
