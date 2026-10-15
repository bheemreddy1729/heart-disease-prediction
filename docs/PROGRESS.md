# Assignment progress

Author: `2025ae05142`

Complete one phase at a time. A phase is complete only when its gate is met; record blockers and evidence here.

| Phase | Status | Gate / evidence |
|---|---|---|
| 0 — Lab baseline | pass | `docs/ENVIRONMENT.md` records the Linux VM baseline. Python 3.12.9 satisfies the >=3.10 gate; Docker and Minikube are installed. GitHub Actions API access returned HTTP 200; workflow execution remains unverified until Phase 5. |
| 1 — Data and EDA | pass | UCI download, preparation, and EDA commands succeeded; 303 rows, target counts 164/139, 6 reported missing feature values, summary, and all three figures verified below. |
| 2 — Features and models | not started | Cross-validated comparison and report include accuracy, precision, recall, and ROC-AUC for each model. |
| 3 — Experiment tracking | not started | Local MLflow has one run per model, required artifacts/tags, and a registered champion. |
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
- `python3 src/data/download_heart.py` succeeded and saved the UCI processed Cleveland source to `data/raw/processed.cleveland.data`; `data/raw/README.md` records the source and local download date.
- `python3 src/data/prepare.py` succeeded and wrote `data/processed/heart.csv`.
- `python3 src/eda/explore.py` succeeded and wrote `reports/eda_summary.md`, `reports/figures/feature_histograms.png`, `reports/figures/correlation_heatmap.png`, and `reports/figures/class_balance.png`.
- Verified source-aligned row count (303), 13 feature columns, target mapping (`0`: 164; `1`: 139), and preservation/reporting of six missing cells (`ca`: 4; `thal`: 2). All three PNGs are non-empty valid PNG files; the summary contains author attribution, missingness, and class counts.
- `python3 -m compileall -q src` and `git diff --check` succeeded.
- Missing feature values are retained in the processed file, not dropped or imputed; missing values are omitted per feature in histograms and pairwise in correlations. The decision and rationale are recorded in `docs/DECISIONS.md`.

**Next:** Review Phase 1 evidence, then send `start phase 2`.
