# Heart disease prediction — project contract

Course: AIMLCZG523 MLOps, Assignment 1 (50 marks).
Repository: https://github.com/bheemreddy1729/heart-disease-prediction
Author tag on every MLflow run, log line, and report header: `2025ae05142`.
Runtime: the BITS Prayogshala Linux VM, not the Windows laptop. Detect `$HOME` and the actual username. Do not assume a cloud account.

## Outcome

A reproducible classifier for the UCI Heart Disease dataset, served as `POST /predict`, tested in CI, packaged in Docker, deployed on local Kubernetes, and monitored well enough to screenshot.

## Stack (do not swap unless a probe fails)

Python 3.12, pandas, scikit-learn, MLflow with a local SQLite store, FastAPI, pytest, ruff, Docker, GitHub Actions, Minikube, Prometheus client metrics. Grafana only if `free -h` shows enough memory.

## Originality

Implement this repository from the assignment requirements and the decisions recorded in `docs/DECISIONS.md`. Do not clone, vendor, or mirror another student's heart-disease MLOps repository, notebook, workflow, Dockerfile, or Kubernetes manifest. When two designs would both pass, pick the one you can justify in the report and write that justification down.

## Working rules

- Read `docs/PROGRESS.md` before doing anything. Update it at the end of every phase.
- Finish one phase and meet its gate before starting the next.
- Probe the VM before installing anything. Prefer user-level installs.
- Never commit secrets, tokens, or cloud credentials.
- Commit or push only when the student explicitly asks.
- Do not add agent co-author trailers to commits.
- If Docker, Minikube, or GitHub Actions is unavailable, stop and report the exact command and error. Do not pretend the phase passed.
- The student records the video and takes the UI screenshots listed in `docs/screenshots/README.md`.
