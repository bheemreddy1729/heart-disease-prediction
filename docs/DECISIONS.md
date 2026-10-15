# Project decisions

Decisions are recorded as each phase reaches its design gate. Do not substitute third-party student implementations for original project work.

## Phase 0

- **Runtime:** Use the BITS Prayogshala Linux VM and its detected user home, `/home/s2025ae05142`. Do not assume a cloud account or move implementation to the Windows laptop.
- **Stack:** Retain the assignment's Python, pandas, scikit-learn, MLflow, FastAPI, pytest, ruff, Docker, GitHub Actions, Minikube, and Prometheus-client stack. The VM has Python 3.12.9, Docker 28.0.1, and Minikube 1.35.0. Reassess individual components only if a concrete compatibility probe fails.
- **Tracking and artifacts:** Use a local SQLite MLflow backend and local file artifacts, as required; do not introduce hosted tracking.
- **Data and target:** Use the UCI Heart Disease processed Cleveland dataset (dataset 45). Treat target value 0 as absence and values 1–4 as presence.
- **Leakage prevention:** Any model imputers, encoders, and scalers must be fit as part of the training pipeline, within training folds where cross-validation is used.
- **Run attribution:** Tag each MLflow run, log line, and report header with `2025ae05142`.
- **Cluster and CI:** Target local Minikube, not a managed Kubernetes service. GitHub Actions is reachable through the repository's Actions API; do not push or trigger a workflow unless explicitly requested.
- **Deferred decisions:** EDA missing-value display/handling, the third classifier, the random seed, champion selection rule, and serving/deployment details will be decided and justified in their relevant phases.
