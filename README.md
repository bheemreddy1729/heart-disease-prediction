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

## HTTP API and Docker

The FastAPI service exposes `POST /predict` with the same JSON list body and
prediction-list response as `predict_records`. Invalid records return HTTP 422.
`GET /health` returns `{"status":"ok"}`. Before building, generate the
gitignored model artifact with `python -m src.train.package`. The inference
image copies this locally generated artifact and pinned serving dependencies;
it does not download data, train, or access MLflow at startup.

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

The port is bound to loopback for local testing. The image runs as an
unprivileged user. Only load trusted locally generated joblib artifacts.

## Kubernetes on Minikube

The local cluster uses the Docker driver and loads a local image; no registry
or cloud credentials are needed. Phase 7's smoke record preserves the Phase 6
image/tag, while the current deployment manifest uses the reviewed Phase 8
image tag. Generate the locally ignored model artifact and build that tag
before applying manifests:

```sh
python -m src.train.package
docker build --tag heart-disease-2025ae05142:phase8-review .
minikube start -p heart-disease --driver=docker --cpus=2 --memory=4096 --disk-size=20g
minikube image load --profile=heart-disease heart-disease-2025ae05142:phase8-review
minikube kubectl -p heart-disease -- apply -f k8s/namespace.yaml
minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/service.yaml
minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api \
  -n heart-disease --timeout=180s
minikube kubectl -p heart-disease -- get pods,services -n heart-disease
minikube service heart-disease-api -p heart-disease -n heart-disease --url
```

The printed URL is the retained NodePort route. To meet the assignment PDF's
Load Balancer or Ingress requirement, the Service now uses `LoadBalancer`.
Run `minikube tunnel -p heart-disease` in a separate VM terminal and keep it
running, then use the Service's assigned `EXTERNAL-IP` for `/health` and
`/predict`. This is local VM access, not a public cloud endpoint. See the
[deployment instructions](docs/DEPLOY.md) and [smoke record](docs/deploy_smoke.md)
for verified deployment and endpoint output.

Current verified captures: [LoadBalancer deployment and responses](screenshots/phase-7-loadbalancer.png)
and [tunnel and request logs](screenshots/phase-7-loadbalancer-tunnel.png).

## Monitoring and logging

The Phase 8 API writes privacy-conscious JSON request events and exposes
Prometheus request-count and latency metrics at `GET /metrics`. Prometheus
scrapes the API every 15 seconds; Grafana provides a provisioned request-rate,
latency, and total-request dashboard. The monitoring stack uses bounded local
Kubernetes resources and loopback-only port-forward access. See
[monitoring and smoke evidence](docs/DEPLOY.md#monitoring-and-logging), including the live
[restored Grafana dashboard screenshot](screenshots/phase-8-restored-grafana.png)
and [workloads and metrics increment](screenshots/phase-8-restored-metrics.png).

## Tests and CI

### Optional tuning follow-up

The separate tuning command evaluates the predeclared nine-configuration RBF
SVC grid using the same fold-local preprocessing and recall-first ranking:

```sh
.venv-phase4/bin/python -m src.train.tune
```

Run it only when ready to append experiments. It writes
`reports/tuning_summary.md` and logs configuration parameters, four CV metrics
and standard deviations, scores, a comparison plot, and report/run IDs in the
separate local `heart-disease-tuning-2025ae05142` MLflow experiment. It does not
register a champion, overwrite baseline reports/models, or change the deployed
API. Scores are tuning/selection results on the reused dataset, not independent
test estimates. Promotion requires a separate review and downstream validation.
The design is recorded in [decisions](docs/DECISIONS.md#model-tuning-follow-up-approved-design-2026-10-19).

### Validation commands

Install development tools into the same isolated environment, then run:

```sh
.venv-phase4/bin/python -m pip install -r requirements-dev.txt
.venv-phase4/bin/python -m pip check
.venv-phase4/bin/python -m ruff check .
.venv-phase4/bin/python -m pytest -q
```

The tests regenerate prepared data from the committed UCI raw snapshot and build
their own calibrated model in temporary directories. They do not require existing
models, MLflow state, or network access, and do not overwrite project artifacts.
They cover data/target validation, fold-local preprocessing, CV metrics and
champion selection, calibration packaging/provenance, and inference contracts
including the exact 0.5 tie, attributed CLI errors, and the HTTP API request and
response contract.

[GitHub Actions](.github/workflows/ci.yml) defines separate `lint`, `test`, and
`train` jobs for pushes, pull requests, and manual dispatch. Training waits for
both checks, regenerates processed data and EDA from the committed raw snapshot,
logs three candidates to a fresh local MLflow store, packages the separate
calibrated serving model, and verifies inference and registry reload. It uploads
reports, models, MLflow state, and sample JSON as the seven-day
`training-evidence-2025ae05142` artifact. MLflow paths inside this evidence point
to the original runner; regenerate locally rather than assuming the downloaded
store is portable. Treat serialized models as trusted-code artifacts, not safe
arbitrary uploads.

Hosted run [38955767909](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38955767909)
passed lint, test, and train at its recorded revision. Local reproduction,
failure/recovery evidence, and historical hosted results are in
[progress](docs/PROGRESS.md); this is not a claim that later unpushed changes
have run on GitHub. New publication/dispatch requires explicit authorization.

## Documentation and results

Written guidance and evidence are consolidated into the documents below; generated results remain in `reports/` with unchanged script and CI paths.

### Submission material

- [Assignment report source](docs/ASSIGNMENT_REPORT.md): coursework narrative, selected results,
  architecture, and genuine screenshots. Still a draft; the final 10-page
  DOC/DOCX/PDF, video link, and upload-size checks remain pending.
- [Screenshot checklist](docs/screenshots/README.md): maps assignment evidence to
  actual captures under [screenshots/](screenshots/). Images are not copied
  into this documentation folder.

### Current setup and operation

| Topic | Canonical guide |
|---|---|
| Installation, data/model reproduction, API, Docker, tests, and tuning commands | [Repository README](#reproduce-on-the-vm) |
| Dataset source, target mapping, and missing values | [Data provenance](docs/DECISIONS.md#data-provenance) |
| Local Kubernetes LoadBalancer access and tunnel lifecycle | [Deployment instructions](docs/DEPLOY.md) |
| Request logging, metrics, Prometheus, and Grafana | [Monitoring guide](docs/DEPLOY.md#monitoring-and-logging) |
| Design rationale, alternatives, and baseline-retention decision | [Project decisions](docs/DECISIONS.md) |

### Generated results

These files in [reports/](reports/) are written by project commands, not
parallel hand-written reports. Use them as the numerical source for the final
report; do not manually edit results to match a preferred outcome.

| Result | Producing command |
|---|---|
| [EDA summary](reports/eda_summary.md) and [figures](reports/figures/) | `.venv-phase4/bin/python src/eda/explore.py` |
| [Model comparison](reports/model_comparison.md) and [MLflow summary](reports/mlflow_summary.md) | `.venv-phase4/bin/python src/train/train.py` |
| [Calibration diagnostics](reports/calibration_summary.md) and reliability figure | `.venv-phase4/bin/python -m src.train.package` |
| [Tuning summary](reports/tuning_summary.md) | `.venv-phase4/bin/python -m src.train.tune` |

Training appends MLflow runs/registry versions; packaging rewrites the local
serving artifact; tuning appends separate experiment runs without promotion.
Reading saved results does not require rerunning these commands. The baseline
model comparison, uncalibrated tuning results, and calibrated serving diagnostics
describe different evaluations and must not be combined as one score.

### Validation and history

- [Progress](docs/PROGRESS.md): phase status, dated commands/outcomes, failures and
  corrections, and approval boundaries; not a second submission report.
- [Docker smoke record](docs/deploy_smoke.md#docker-container-smoke-evidence): actual container build/run proof.
- [Deployment smoke record](docs/deploy_smoke.md): current LoadBalancer evidence and
  explicitly retained historical NodePort checks.
- [Monitoring restoration](docs/DEPLOY.md#restored-monitoring-verification-2026-10-19):
  current validation and captures; earlier monitoring records are historical.
- [Environment baseline](docs/DECISIONS.md#historical-vm-baseline): original VM probe, not a guarantee
  that a later VM has identical state.

Preserve genuine historical evidence, but use current LoadBalancer and restored
monitoring captures for the submission. The final PDF should contain its key
results and access instructions rather than require the reader to follow local
filesystem links.
