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

- Originality means independent implementation and evidence-based reasoning, not choosing unusual techniques merely to appear unique.
- Before implementing a design choice, record the choice, its rationale, relevant alternatives, and any external sources in `docs/DECISIONS.md`. Cite adapted material and respect its license.
- If a proposed step risks copying, lacks a defensible rationale, or deviates from the assignment, explain the concern and pause for the student's decision before proceeding.
- Follow the course's AI-assistance disclosure requirements. Omitting agent co-author trailers does not replace required disclosure.

## Working rules

- Read `docs/PROGRESS.md` before doing anything. Update it at the end of every phase.
- Finish one phase and meet its gate before starting the next.
- Stop after each phase for student review unless the student explicitly requests `run all`. Prefer logically complete, atomic commits; commit and push only with explicit permission.
- Probe the VM before installing anything. Prefer user-level installs.
- Run assignment installation, training, tests, containers, and deployment on the VM. Windows-side documentation reviews are allowed, but must not be reported as live VM validation.
- Record the validation command, execution location, key output, and any failure for each gate. Endpoint access or an installed CLI is not proof that a workflow, container, or cluster ran successfully.
- Include `Author: 2025ae05142` in document/report headers. Use only `not started`, `in progress`, `pass`, or `blocked` for phase states.
- Never commit secrets, tokens, or cloud credentials.
- Commit or push only when the student explicitly asks.
- Do not add agent co-author trailers to commits.
- If Docker, Minikube, or GitHub Actions is unavailable, stop and report the exact command and error. Do not pretend the phase passed.
- The student records the video and takes the UI screenshots listed in `docs/screenshots/README.md`.
