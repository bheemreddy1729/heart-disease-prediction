# Heart Disease Prediction: MLOps Assignment 1

Author: `2025ae05142`

Course: AIMLCZG523  
Repository: [bheemreddy1729/heart-disease-prediction](https://github.com/bheemreddy1729/heart-disease-prediction)

## Executive summary

This project implements a reproducible machine-learning workflow for the
processed Cleveland subset of the UCI Heart Disease dataset. It prepares and
profiles the data, compares three classifiers with leakage-safe cross-validation,
tracks model experiments locally with MLflow, packages a calibrated serving
pipeline, exposes predictions through a FastAPI endpoint, and runs that API in
a local Minikube deployment. GitHub Actions checks the code and reproduces the
training workflow. Prometheus metrics, privacy-conscious request logs, and a
Grafana dashboard provide operational visibility.

The workflow has evidence for each stage in the repository. Those records show
that the project ran on the BITS Prayogshala Linux VM, the hosted CI workflow
completed successfully, and the local Kubernetes service returned predictions.
The evaluation is coursework evidence, not clinical validation or a claim that
the model is appropriate for diagnosis or treatment.

## 1. Scope and reproducible environment

The objective was to connect data processing, model development, packaging,
serving, testing, CI, deployment, and monitoring into one traceable workflow
without requiring cloud accounts. Implementation and runtime validation were
performed on the BITS Prayogshala Linux VM as user `s2025ae05142`, in the
repository at `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`.
The recorded environment includes Python, Docker, and Minikube. The VM did not
have standalone `kubectl`; deployment commands used the compatible client
bundled with Minikube. See the [environment
record](./DECISIONS.md#historical-vm-baseline) and [progress evidence](./PROGRESS.md).

The following sequence follows the repository's [README](../README.md). It
creates an isolated Python environment, installs the pinned dependencies,
checks dependency consistency, regenerates the data and reports, trains and
packages the model, then exercises the sample inference command:

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

The documented inference result is a JSON list. Each item has an integer
`prediction` (`0` for absent or `1` for present) and a floating-point
`confidence`, defined as the probability assigned to the predicted class. The
sample input is a feature-only dataset record, not an independent test case.
The model artifact is generated locally and is intentionally not checked into
the repository. Only trusted locally generated joblib/MLflow artifacts should
be loaded because serialized Python objects can execute code.

## 2. Dataset and exploratory analysis

The data source is the [UCI Heart Disease processed Cleveland dataset](https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data),
using the processed Cleveland file. It contains 303 patient records, 13
clinical feature columns, and the original `num` outcome. Preparation maps
`num=0` to absence (`0`) and original values `1` through `4` to presence (`1`).
The source's `?` values are retained as missing rather than dropping records or
estimating values during EDA. The [data provenance note](./DECISIONS.md#data-provenance) records the
source, download date, and preparation commands.

The target distribution is 164 absent and 139 present records. Six feature
cells are missing: four in `ca` and two in `thal`; the other reported columns
have no missing cells. The [EDA summary](../reports/eda_summary.md) records
these counts and the generated figures. Histograms omit missing values for
each individual feature, and the correlation calculation uses pairwise
complete observations. These choices keep the complete source cohort visible
without allowing imputation statistics to use data before model validation.

For modelling, five measurements (`age`, `trestbps`, `chol`, `thalach`, and
`oldpeak`) are treated as continuous numeric features. Eight coded features
(`sex`, `cp`, `fbs`, `restecg`, `exang`, `slope`, `ca`, and `thal`) are treated
as categorical values. The detailed rationale—including why missing values
are not imputed in the EDA stage—is recorded in [design decisions](./DECISIONS.md).

## 3. Candidate models and validation

Three model families were compared: Logistic Regression, Random Forest, and an
RBF-kernel Support Vector Classifier. Logistic Regression provides a regularized
linear baseline, Random Forest can represent nonlinear splits and interactions,
and the RBF SVC tests a smooth nonlinear boundary. This comparison is appropriate
for exploring different decision structures on a small tabular dataset; it is
not evidence that one algorithm is universally superior.

Each candidate is evaluated through a scikit-learn pipeline. Continuous
features use median imputation and standardization. Categorical features use
most-frequent imputation followed by one-hot encoding, with unknown categories
ignored at inference. These transformations are fit within each training fold,
not on the full dataset before validation. Five-fold stratified cross-validation
uses shuffling and `random_state=42`; accuracy, precision, recall, and ROC-AUC
are reported as fold means and sample standard deviations.

The project prioritizes mean recall because missed positive cases are the
primary screening error of concern. Mean ROC-AUC and then mean precision break
recall ties; accuracy is reported but does not determine the winner. By that
rule, `rbf_svc` is the champion:

| Candidate | Accuracy | Precision | Recall | ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.8547 ± 0.0542 | 0.8744 ± 0.0640 | 0.7979 ± 0.0812 | 0.9188 ± 0.0232 |
| Random Forest | 0.8384 ± 0.0310 | 0.8505 ± 0.0612 | 0.7913 ± 0.0306 | 0.9144 ± 0.0255 |
| RBF SVC | 0.8448 ± 0.0506 | 0.8501 ± 0.0666 | 0.8056 ± 0.0656 | 0.9021 ± 0.0319 |

These are cross-validation estimates on a small dataset. Candidate selection
used the same dataset, and there is no claim here of an independent test-set
estimate or clinical performance. The complete comparison and champion rule
are in [model_comparison.md](../reports/model_comparison.md).

### Hyperparameter tuning and deployment decision

After the initial model-family comparison, a bounded RBF SVC tuning experiment
evaluated nine combinations: `C` in `{0.1, 1, 10}` and `gamma` in
`{"scale", 0.01, 0.1}`. This grid explores regularization strength and kernel
width, including the original `C=1, gamma="scale"` baseline. All configurations
used the same five shuffled stratified folds, seed 42, and fold-local
preprocessing. Selection followed the existing recall-first rule, with ROC-AUC
and precision as tie-breakers. The separate local MLflow experiment
`heart-disease-tuning-2025ae05142` contains the completed runs, parameters,
metrics, comparison plot, and report.

| Uncalibrated RBF SVC configuration | Accuracy | Precision | Recall | ROC-AUC |
|---|---:|---:|---:|---:|
| Original: C=1, gamma=scale | 0.844754 | 0.850069 | 0.805556 | 0.902143 |
| Tuning winner: C=1, gamma=0.1 | 0.848033 | 0.851656 | 0.812698 | 0.901927 |

Values are CV means; standard deviations, all configurations, and actual run
IDs appear in [the tuning summary](../reports/tuning_summary.md). The selected
configuration's run ID is `05e2a3643a7444788a4945f2e8d6b9ad`. Its recall mean
increased by `0.007143`, while ROC-AUC decreased by `0.000216`, calculated from
unrounded results. The original candidate selection and tuning reuse the same
dataset; these are selection results, not independent evidence of improved
generalization or a global optimum.

Following review, the deployment decision was to retain the existing validated
calibrated baseline. The tuning winner remains the winner of the declared grid
ranking, but has not been calibrated, packaged, or promoted. A small reused-data
CV gain does not by itself justify replacing the validated serving artifact.
These uncalibrated tuning scores must not be confused with the separate
calibrated probability diagnostics below. Any future promotion would require
additional evaluation and full downstream validation.

## 4. Experiment tracking and packaged confidence

Training writes MLflow runs to a repository-local SQLite tracking and registry
store, with model files and figures in a local artifact directory. This keeps
the experiment workflow usable without a hosted tracking service. The latest
recorded successful candidate batch and champion registry version are
summarized in [mlflow_summary.md](../reports/mlflow_summary.md):

| Model | Run ID | Logged model URI |
|---|---|---|
| Logistic Regression | `e31403f4bb7d4506b39ceb1ff05004c4` | `models:/m-b5fd21e8ba934af496d60383792f11d2` |
| Random Forest | `278a020c22ae4530aabafb6bd5fc1307` | `models:/m-01a5af4d0b6c48ce82d5cea6cbb03c72` |
| RBF SVC | `5ad5e00bd4714b998beb1b868379a2b2` | `models:/m-bfd6e6c8994c44298d525deb69be3746` |

The experiment records include author attribution, data identity, model and
preprocessing parameters, validation metrics, fitted pipelines, and EDA
artifacts. The uncalibrated candidate champion is registered as
`heart-disease-champion-2025ae05142`, version 2. This registry model and the
calibrated serving artifact are separate: the serving artifact does not
overwrite or relabel the registry candidate's metrics.

For serving probabilities, packaging wraps the selected full preprocessing
and classifier pipeline in a sigmoid `CalibratedClassifierCV`. The recorded
evaluation uses five outer stratified folds and five inner calibration folds,
with shuffling and seed 42. After out-of-fold evaluation, the final pipeline
is fit on all 303 records and saved with provenance. The
[calibration summary](../reports/calibration_summary.md) reports pooled
out-of-fold accuracy `0.854785`, precision `0.851852`, recall `0.827338`,
ROC-AUC `0.905115`, Brier score `0.121745`, log loss `0.392889`, and a
training-fold prevalence baseline Brier score of `0.248313`.

These diagnostics are post-selection because candidate selection used this
dataset. They do not establish independent generalization, perfect calibration,
clinical suitability, or a treatment threshold. Inference predicts class 1
when disease probability is greater than `0.5`; otherwise it predicts class
0. An exact tie at `0.5` returns class 0 because the validated class order is
`[0, 1]`. The returned confidence is the probability of the chosen class, not
certainty.

## 5. System architecture

The data, experiment, packaging, deployment, and monitoring paths are separated
so the serving container does not download data, train a model, or access
MLflow at startup.

```mermaid
flowchart LR
    UCI["UCI processed Cleveland data"] --> Prep["Prepare and validate"]
    Prep --> EDA["EDA summaries and figures"]
    Prep --> Train["Cross-validation and candidate pipelines"]
    Train --> Compare["Model comparison report"]
    Train --> MLflow["Local MLflow SQLite store<br/>runs and registry"]
    Train --> Package["Sigmoid calibration and final fit"]
    Package --> Artifact["Local joblib pipeline<br/>and provenance"]
    Artifact --> API["FastAPI<br/>POST /predict"]
    API --> Image["Inference Docker image"]
    Image --> K8s["Minikube Deployment<br/>LoadBalancer Service"]
    Tunnel["minikube tunnel<br/>VM-local access"] --> K8s
    API --> Logs["JSON request logs"]
    API --> Metrics["Prometheus /metrics"]
    Metrics --> Prom["Prometheus scrape"]
    Prom --> Grafana["Grafana dashboard"]
    CI["GitHub Actions<br/>lint, test, train"] --> Train
    CI --> Artifact
```

The diagram summarizes the implementation represented by the repository; it
does not imply that training occurs inside Minikube or that MLflow is a serving
dependency. The source code, manifests, workflow, and smoke records provide the
implementation details.

## 6. API and container

The FastAPI application exposes `GET /health` and `POST /predict`. The prediction
endpoint accepts the same feature-only JSON list used by local inference and
returns prediction/confidence pairs. Invalid request records are rejected with
HTTP 422. The inference-only Docker image includes the generated model artifact
and serving dependencies, runs as unprivileged UID 10001, and is bound to
loopback for the recorded local smoke test.

On the VM, the Phase 6 image build succeeded. `GET /health` returned
`{"status":"ok"}` and a `POST /predict` using `examples/patient.json` returned
`[{"prediction":0,"confidence":0.7466949562461239}]`. The recorded container
ran as user `app` (UID 10001), and the temporary smoke-test container was
stopped and removed after verification. Full commands and output are in
[deploy_smoke.md#docker-container-smoke-evidence](./deploy_smoke.md#docker-container-smoke-evidence).

## 7. Kubernetes deployment

The deployment uses a single-node local Minikube cluster with the Docker driver.
The locally built image is loaded into the cluster rather than pulled from a
public registry. A namespace, one-replica Deployment, and LoadBalancer Service
provide local API access through `minikube tunnel`; health probes use `/health`.
The Service retains nodePort `30080` as an additional route. This design avoids
cloud accounts and meets the assignment PDF's Load Balancer or Ingress
requirement. NodePort alone, used in the initial deployment, did not meet that
exposure requirement.

The corrected deployment was verified on the current VM with `minikube tunnel`
running. Its LoadBalancer external address was `10.97.154.192`; health returned
`{"status":"ok"}` and sample prediction returned
`[{"prediction":0,"confidence":0.7466949562461239}]`.
The API pod was ready with zero restarts and the retained NodePort route still
worked. These are local Minikube observations, not a claim of a public or
production cloud load balancer. The
[LoadBalancer correction evidence](./deploy_smoke.md#loadbalancer-correction-2026-10-19)
records the commands and results. To reproduce local access, follow
[the deployment instructions](./DEPLOY.md), keeping the tunnel running.

![Live VM LoadBalancer deployment and endpoint checks](../screenshots/phase-7-loadbalancer.png)

The genuine terminal capture above shows the ready API pod, LoadBalancer
external address, health response, and prediction. The additional
[tunnel and request-log capture](../screenshots/phase-7-loadbalancer-tunnel.png)
shows the running local tunnel, route, sample request, and attributed event.

## 8. CI, testing, and reproducibility

The GitHub Actions workflow in `.github/workflows/ci.yml` has separate `lint`,
`test`, and `train` jobs. The hosted train job reproduces processing and EDA
from the committed raw data, evaluates and tracks the model candidates,
packages the calibrated serving model, verifies outputs, and uploads a
training evidence artifact. The test suite builds test artifacts in temporary
locations rather than relying on ignored model or MLflow files. Local
reproduction commands, test outcomes, and workflow limitations are recorded
in [PROGRESS.md](./PROGRESS.md).

The project includes a deliberate CI failure and its recovery: an explicitly
added assertion failed, then the workflow returned to green after that test
was reverted. The [Phase 5 failure/recovery record](./PROGRESS.md#phase-5-review-correction-deliberate-failure-followed-by-revert)
documents the actual hosted runs and screenshots. Later, an initial Phase 8
hosted run exposed a clean-runner test dependency on an ignored local model
artifact; the test was corrected to use an isolated fixture, as detailed in
the [Phase 8 review correction](./PROGRESS.md#phase-8-review-correction). The
[verified hosted Actions run](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38955767909)
completed successfully on `main`. GitHub reports successful `lint`, `test`,
and `train` jobs, and the training evidence artifact
`training-evidence-2025ae05142` was uploaded.

That hosted run is evidence that the workflow succeeded at the recorded
revision. The earlier failing runs are retained as diagnostic evidence; they
are not presented as successful runs. The detailed job and artifact evidence,
along with local Ruff and pytest results, is in [PROGRESS.md](./PROGRESS.md).

## 9. Monitoring and request privacy

The API emits one JSON log event per `POST /predict`, including UTC timestamp,
feature names, prediction, confidence, latency, and the author tag. Feature
values and free-text bodies are not logged. Invalid bodies are logged with
empty feature names and null prediction/confidence. The Prometheus client
exposes a request counter and latency histogram without patient data or
request-specific labels.

Prometheus scrapes the API every 15 seconds. The provisioned Grafana dashboard
shows request rate, latency percentiles, and total requests. In the recorded
Phase 8 deployment, the API, Prometheus, and Grafana pods were each `1/1
Running` with zero restarts. The live API returned HTTP 200 for the sample and
HTTP 422 for invalid requests; request counters and histogram observations
increased as expected. Prometheus reported the API target up with no scrape
error, and Grafana loaded the provisioned dashboard. The review-correction
validation checked a valid request, malformed JSON, and a missing body, with
the counter and histogram each increasing exactly once per request. See
[DEPLOY.md#monitoring-and-logging](./DEPLOY.md#monitoring-and-logging) for commands, actual outputs, privacy details,
resource observations, and links to real screenshots.

After the LoadBalancer correction, the existing Prometheus/Grafana workloads
were restored and reverified on the current VM. All three pods were ready with
zero restarts, the scrape target was up, and valid and rejected requests each
incremented the API counter and latency observation exactly once. No monitoring
code change was needed because the internal Service scrape address stayed the
same. The [restoration record](./DEPLOY.md#restored-monitoring-verification-2026-10-19)
distinguishes these current checks from the historical execution.

![Restored Grafana dashboard with live request and latency data](../screenshots/phase-8-restored-grafana.png)

## 10. Limitations and responsible interpretation

This project is an educational MLOps exercise, not a medical device. The
dataset is a small processed subset, validation is cross-validation on the
same data used for candidate selection, and no independent clinical cohort or
prospective study is reported. Performance numbers are not guarantees for
other populations, care settings, or future patients. Calibration diagnostics
are also post-selection estimates, not proof of clinical calibration.

The fixed probability threshold is a project decision, not a clinically
optimized operating point. A prediction or confidence value must not be used
as a diagnosis, treatment recommendation, or substitute for a qualified
clinician. Further work would require appropriately governed data, independent
evaluation, clinical review, security/privacy review, and validation under the
intended deployment conditions. Those activities are outside this assignment's
verified scope.

## Evidence index

- [Data source and preparation](./DECISIONS.md#data-provenance)
- [Design rationale and alternatives](./DECISIONS.md)
- [EDA summary and figures](../reports/eda_summary.md)
- [Model comparison](../reports/model_comparison.md)
- [Hyperparameter tuning results](../reports/tuning_summary.md)
- [MLflow run summary](../reports/mlflow_summary.md)
- [Calibration diagnostics](../reports/calibration_summary.md)
- [Docker smoke record](./deploy_smoke.md#docker-container-smoke-evidence)
- [Kubernetes smoke record](./deploy_smoke.md)
- [Monitoring and logging evidence](./DEPLOY.md#monitoring-and-logging)
- [Phase-by-phase validation record](./PROGRESS.md)
