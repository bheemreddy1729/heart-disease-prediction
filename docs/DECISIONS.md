# Project decisions

Author: `2025ae05142`

Decisions are recorded as each phase reaches its design gate. Do not substitute third-party student implementations for original project work.

## Phase 0

- **Runtime:** Use the BITS Prayogshala Linux VM and its detected user home, `/home/s2025ae05142`. Do not assume a cloud account or move implementation to the Windows laptop.
- **Stack:** Retain the assignment's Python, pandas, scikit-learn, MLflow, FastAPI, pytest, ruff, Docker, GitHub Actions, Minikube, and Prometheus-client stack. The VM has Python 3.12.9, Docker 28.0.1, and Minikube 1.35.0. Reassess individual components only if a concrete compatibility probe fails.
- **Tracking and artifacts:** Use a local SQLite MLflow backend and local file artifacts, as required; do not introduce hosted tracking.
- **Data and target:** Use the UCI Heart Disease processed Cleveland dataset (dataset 45). Treat target value 0 as absence and values 1–4 as presence.
- **Leakage prevention:** Any model imputers, encoders, and scalers must be fit as part of the training pipeline, within training folds where cross-validation is used.
- **Run attribution:** Tag each MLflow run, log line, and report header with `2025ae05142`.
- **Cluster and CI:** Target local Minikube on the assigned VM to keep deployment reproducible without requiring a public-cloud account. The repository's Actions API is reachable, but workflow execution remains unverified until Phase 5; do not push or trigger a workflow unless explicitly requested.
- **Deferred decisions:** EDA missing-value display/handling, the third classifier, the random seed, champion selection rule, and serving/deployment details will be decided and justified in their relevant phases.

## Phase 1

- **EDA missingness:** Preserve source `?` values as missing in the processed table, report missing counts, and do not drop rows or impute during EDA. This keeps all 303 records available and avoids fitting imputation statistics before the training split. Histograms omit missing values within each feature; the correlation matrix uses pairwise complete observations. Fit any later imputer only on training data as part of the model pipeline.
- **Target:** Map original Cleveland `num=0` to absence (`0`) and `num=1,2,3,4` to presence (`1`); reject target values outside this defined domain.
- **EDA scope:** Plot histograms for the 13 numeric clinical features (not the outcome), use Pearson correlations across those features, and show class counts after binarization.
- **Reproducibility:** Download the processed Cleveland file from the UCI URL documented in `docs/DATA.md`; retain its local raw copy and record its download date. Pin only the pandas and matplotlib dependencies needed by this phase; extend the manifest when later phases need their dependencies.
