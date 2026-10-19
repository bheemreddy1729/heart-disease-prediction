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
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip check
.venv/bin/python src/data/download_heart.py
.venv/bin/python src/data/prepare.py
.venv/bin/python src/eda/explore.py
.venv/bin/python src/train/train.py
.venv/bin/python -m src.train.package
.venv/bin/python -m src.infer.predict --input examples/patient.json
```

The last command prints a JSON list with an integer `prediction`
(0 = absent, 1 = present) and a `confidence` between 0 and 1 for that class.
The sample in `examples/patient.json` is a record from the dataset, so treat it
as a smoke test rather than an unseen patient.

The model predicts 1 when P(disease) > 0.5. An exact 0.5 returns class 0 with
confidence 0.5, because `argmax` picks the first class in `[0, 1]`.

Each training run adds three MLflow runs and a new registered version of the
uncalibrated champion, and writes [the comparison](reports/model_comparison.md)
and [MLflow summary](reports/mlflow_summary.md). `mlflow.db` and `mlruns/` stay
local and are gitignored.

Packaging repeats the model selection, wraps the chosen pipeline in a sigmoid
calibrator, checks it with nested 5×5 cross-validation, and then fits it on all
rows. It writes:

- `models/heart_pipeline.joblib`: the full pipeline used for serving;
- `models/heart_pipeline.json`: data and artifact hashes, versions, settings, and metrics;
- [calibration diagnostics](reports/calibration_summary.md) and its reliability figure.

The calibrated model is saved separately; it does not replace the registered
uncalibrated model in MLflow.

## Python inference

```python
import json
from pathlib import Path
from src.infer.predict import predict_records

records = json.loads(Path("examples/patient.json").read_text())
predictions = predict_records(records)
```

Each record needs exactly the 13 feature keys from the sample. Values must be
numbers or `null`; nulls are filled by the fitted imputers, while missing or
extra keys, strings, booleans, and NaN/infinity are rejected. The CLI exits
with a non-zero code and an error message on bad input. Only load model files
you generated yourself, since joblib/pickle loading can run code.

## HTTP API and Docker

The FastAPI service exposes `POST /predict`, which takes the same JSON list as
`predict_records` and returns the predictions. Invalid records return HTTP 422.
`GET /health` returns `{"status":"ok"}`. Run `python -m src.train.package`
before building, because the image copies the model file from `models/`.

```sh
docker build --tag heart-disease-2025ae05142:phase6 .
docker run --rm --detach --name heart-disease-2025ae05142 \
  --publish 127.0.0.1:8000:8000 heart-disease-2025ae05142:phase6
curl --fail-with-body --silent --show-error http://127.0.0.1:8000/health
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @examples/patient.json http://127.0.0.1:8000/predict
docker stop heart-disease-2025ae05142
```

The port is bound to `127.0.0.1` only, and the container runs as a non-root user.

## Kubernetes on Minikube

The API runs on a local Minikube cluster (Docker driver) behind a
`LoadBalancer` Service. No registry or cloud account is needed: the image is
built and loaded locally. Generate the model artifact (it is gitignored), build
the image, and deploy:

```sh
python -m src.train.package
docker build --tag heart-disease-2025ae05142:phase8-review .
minikube start -p heart-disease --driver=docker --cpus=2 --memory=4096 --disk-size=20g
minikube image load --profile=heart-disease heart-disease-2025ae05142:phase8-review
minikube kubectl -p heart-disease -- apply -f k8s/namespace.yaml
minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/service.yaml
minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api \
  -n heart-disease --timeout=180s
```

In a second terminal, start the tunnel and leave it running (it may ask for
sudo to add a local route):

```sh
minikube tunnel -p heart-disease
```

Back in the first terminal, wait until the Service has an `EXTERNAL-IP`
(not `<pending>`), then call the API through it:

```sh
minikube kubectl -p heart-disease -- get pods,services -n heart-disease
LB_IP=$(minikube kubectl -p heart-disease -- get service heart-disease-api \
  -n heart-disease -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl --fail-with-body --silent --show-error --noproxy '*' "http://$LB_IP/health"
curl --fail-with-body --silent --show-error --noproxy '*' \
  -H 'Content-Type: application/json' \
  --data-binary @examples/patient.json "http://$LB_IP/predict"
```

On my VM the address was `http://10.97.154.192`; it can change when the
cluster is recreated. The address is reachable from the VM only, not publicly.
Stop the tunnel with Ctrl-C when finished. The Service also keeps nodePort
`30080`, reachable via
`minikube service heart-disease-api -p heart-disease -n heart-disease --url`.

Screenshots: [LoadBalancer deployment and responses](screenshots/phase-7-loadbalancer.png)
and [tunnel and request logs](screenshots/phase-7-loadbalancer-tunnel.png).

## Monitoring and logging

- Each `POST /predict` writes one JSON log line: author tag, UTC timestamp,
  feature names (not values), prediction, confidence, and latency in ms.
  Invalid or malformed requests are logged too, with null prediction.
- `GET /metrics` exposes `heart_disease_prediction_requests_total` and the
  `heart_disease_prediction_request_duration_seconds` histogram, with no
  patient data in labels.
- Prometheus scrapes the API Service every 15 seconds; Grafana loads a
  provisioned dashboard with request rate, p50/p95 latency, and total requests.

Deploy the monitoring stack after the API. The ConfigMaps are built from the
files in `monitoring/`; the Grafana password goes into a Secret you create on
the VM and never commit:

```sh
minikube kubectl -p heart-disease -- create configmap prometheus-config \
  -n heart-disease --from-file=prometheus.yml=monitoring/prometheus.yml \
  --dry-run=client -o yaml | minikube kubectl -p heart-disease -- apply -f -
minikube kubectl -p heart-disease -- create configmap grafana-datasource \
  -n heart-disease --from-file=grafana-datasource.yaml=monitoring/grafana-datasource.yaml \
  --dry-run=client -o yaml | minikube kubectl -p heart-disease -- apply -f -
minikube kubectl -p heart-disease -- create configmap grafana-dashboard-provider \
  -n heart-disease --from-file=grafana-dashboard-provider.yaml=monitoring/grafana-dashboard-provider.yaml \
  --dry-run=client -o yaml | minikube kubectl -p heart-disease -- apply -f -
minikube kubectl -p heart-disease -- create configmap grafana-dashboard \
  -n heart-disease --from-file=heart-disease-dashboard.json=monitoring/heart-disease-dashboard.json \
  --dry-run=client -o yaml | minikube kubectl -p heart-disease -- apply -f -
read -rsp 'Grafana admin password: ' GF_PW; echo
minikube kubectl -p heart-disease -- create secret generic grafana-admin \
  -n heart-disease --from-literal=admin-password="$GF_PW" \
  --dry-run=client -o yaml | minikube kubectl -p heart-disease -- apply -f -
unset GF_PW
minikube kubectl -p heart-disease -- apply -f k8s/monitoring.yaml
minikube kubectl -p heart-disease -- rollout status deployment/prometheus \
  -n heart-disease --timeout=180s
minikube kubectl -p heart-disease -- rollout status deployment/grafana \
  -n heart-disease --timeout=180s
```

Open the UIs from the VM with port-forwards (one per terminal, left running):

```sh
minikube kubectl -p heart-disease -- port-forward --address=127.0.0.1 \
  service/prometheus 19090:9090 -n heart-disease
minikube kubectl -p heart-disease -- port-forward --address=127.0.0.1 \
  service/grafana 13000:3000 -n heart-disease
```

Prometheus is then at `http://127.0.0.1:19090` and Grafana at
`http://127.0.0.1:13000`; anonymous Grafana access is read-only.

Screenshots: [Grafana dashboard](screenshots/phase-8-restored-grafana.png) and
[workloads and metrics increment](screenshots/phase-8-restored-metrics.png).

## Tests and CI

Install development tools into the same isolated environment, then run:

```sh
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -m ruff check .
.venv/bin/python -m pytest -q
```

The tests build their own data and model in temporary folders from the
committed raw file, so they need no network, MLflow state, or existing model.
They cover target mapping, fold-local preprocessing, CV metrics and champion
selection, calibration packaging, the 0.5 tie, CLI errors, and the API.

[GitHub Actions](.github/workflows/ci.yml) runs `lint`, `test`, and `train` jobs
on every push and pull request (and manually). The `train` job runs only after
the first two pass. It rebuilds the data and EDA, trains the three models into a
fresh MLflow store, packages the calibrated model, checks a prediction, and
uploads everything as the `training-evidence-2025ae05142` artifact (kept seven
days).

Hosted run [38955767909](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38955767909)
passed lint, test, and train. To show that a failing test blocks the pipeline,
run [38789263010](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38789263010)
failed on a deliberate assertion and
[38789471935](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38789471935)
passed after it was reverted.

## Optional model tuning

A separate command tries nine `C`/`gamma` settings for the RBF SVC with the
same folds and recall-first ranking:

```sh
.venv/bin/python -m src.train.tune
```

It logs each setting to its own MLflow experiment,
`heart-disease-tuning-2025ae05142`, and writes `reports/tuning_summary.md`. It
does not register a model or touch the deployed one; see
[design decisions](#design-decisions) for why I kept the baseline.

## Design decisions

**Data and labels.** I used the UCI Heart Disease processed Cleveland file
(dataset 45), downloaded on 2026-10-15 from
<https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data>
into `data/raw/`. The original `num` outcome is binarised: 0 means absence and
1–4 mean presence. Any other value is rejected.

**Missing values.** The six `?` cells (four in `ca`, two in `thal`) stay blank
in `data/processed/heart.csv`. Dropping those rows would discard usable
patients, and imputing before the split would leak information from validation
rows. EDA plots skip blanks per feature, correlations use pairwise complete
rows, and imputation happens only inside the training pipeline for each fold.

**Features.** `age`, `trestbps`, `chol`, `thalach`, and `oldpeak` are treated as
continuous (median imputation, standard scaling). The other eight columns are
clinical codes, so they get most-frequent imputation and one-hot encoding;
scaling them would imply a distance between categories that does not exist.
All of this lives in one scikit-learn `Pipeline`, so serving uses exactly the
preprocessing that was fitted in training.

**Models and selection.** Logistic Regression is the linear baseline, Random
Forest captures splits and interactions, and an RBF SVC tests a smooth
nonlinear boundary. All three use five-fold stratified CV with
`random_state=42`; with only 303 rows, a single train/test split would make the
ranking depend too much on one small sample. The champion is the model with
the highest mean recall, because a missed disease case is the worst error
here, with ROC-AUC and then precision as tie-breakers. Accuracy is reported
but does not pick the winner.

**Confidence and threshold.** Raw SVC scores are not probabilities, so the
served model wraps the whole pipeline in a sigmoid `CalibratedClassifierCV`
(five folds, seed 42). Calibration quality was checked with nested
out-of-fold predictions (Brier score, log loss, reliability curve). I kept the
default 0.5 threshold; picking a clinical threshold would need input this
project doesn't have.

**Tuning.** A small, predeclared grid (`C` in {0.1, 1, 10}, `gamma` in
{scale, 0.01, 0.1}) was run on the RBF SVC using the same folds and ranking.
`C=1, gamma=0.1` won by +0.007 recall but lost 0.0002 ROC-AUC on reused data,
so I kept the already calibrated and deployed baseline instead of promoting it.

**Serving and deployment.** The Docker image installs only the serving
requirements and copies the API and the locally generated model, then runs as
a non-root user, so it never trains or downloads data at startup. I used
Minikube on the VM because the assignment does not require a cloud account.
The Service is a `LoadBalancer` reached through `minikube tunnel`, which meets
the Load Balancer or Ingress requirement; my first version used NodePort only,
and I changed it after rechecking the brief. I did not choose an Ingress
controller because it adds setup for a single API, and Minikube's bundled
ingress-nginx has been retired.

**Monitoring.** Logs keep feature names but never feature values, and metrics
carry no per-request labels, so no patient data leaves the API. Telemetry runs
in middleware so that malformed requests, which FastAPI rejects before the
endpoint, are still counted. The VM had about 10 GiB free memory, so I ran
Prometheus and Grafana with small resource limits.

References: [scikit-learn pipelines](https://scikit-learn.org/stable/modules/compose.html),
[cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html),
[probability calibration](https://scikit-learn.org/stable/modules/calibration.html),
[grid search](https://scikit-learn.org/stable/modules/grid_search.html),
[MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/),
[Minikube LoadBalancer access](https://minikube.sigs.k8s.io/docs/handbook/accessing/#loadbalancer-access),
[ingress-nginx retirement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/),
[Prometheus Python client](https://prometheus.github.io/client_python/), and
[Grafana provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/).

## Documentation and results

### Report

- [Assignment report](docs/ASSIGNMENT_REPORT.md): setup, results, architecture,
  screenshots, and the demonstration video link.
- [Report PDF](docs/ASSIGNMENT_REPORT.pdf): the 10-page version submitted.

### Generated results

Everything in [reports/](reports/) is written by the scripts below; the numbers
in the report come from these files.

| Result | Producing command |
|---|---|
| [EDA summary](reports/eda_summary.md) and [figures](reports/figures/) | `.venv/bin/python src/eda/explore.py` |
| [Model comparison](reports/model_comparison.md) and [MLflow summary](reports/mlflow_summary.md) | `.venv/bin/python src/train/train.py` |
| [Calibration diagnostics](reports/calibration_summary.md) and reliability figure | `.venv/bin/python -m src.train.package` |
| [Tuning summary](reports/tuning_summary.md) | `.venv/bin/python -m src.train.tune` |

The baseline comparison, the tuning results, and the calibration diagnostics
come from different evaluations, so their scores are not directly comparable.

### Screenshots

Evidence captures from the VM and GitHub are in [screenshots/](screenshots/),
named by phase (for example `phase-6-predict.png`,
`phase-7-loadbalancer.png`, `phase-8-restored-grafana.png`).
