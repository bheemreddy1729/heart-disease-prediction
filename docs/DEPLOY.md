# Kubernetes deployment

Author: `2025ae05142`

This project deploys its locally built serving image to Minikube with the Docker
driver. The `heart-disease-api` Service is a `LoadBalancer`, meeting the
assignment PDF's Load Balancer or Ingress requirement. Minikube supplies local
LoadBalancer access through a tunnel; no cloud account or public registry is
required. The retained nodePort `30080` is an additional local access route,
not the basis for claiming compliance.

Generate the trusted local model using the [README instructions](../README.md)
if it is absent, then build and deploy the image used by the manifest:

```sh
docker build --tag heart-disease-2025ae05142:phase8-review .
minikube start -p heart-disease --driver=docker --cpus=2 --memory=4096 --disk-size=20g
minikube image load --profile=heart-disease heart-disease-2025ae05142:phase8-review
minikube kubectl -p heart-disease -- apply -f k8s/namespace.yaml
minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/service.yaml
minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api \
  -n heart-disease --timeout=180s
```

In a separate VM terminal, run the tunnel and leave it running. It may request
sudo permission to configure the local route:

```sh
minikube tunnel -p heart-disease
```

In the original terminal, wait until `EXTERNAL-IP` is assigned (not `<pending>`),
then obtain the LoadBalancer URL. Do not run a second tunnel if one is already
active for this profile:

```sh
minikube kubectl -p heart-disease -- get pods,services -n heart-disease
LB_IP=$(minikube kubectl -p heart-disease -- get service heart-disease-api \
  -n heart-disease -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
test -n "$LB_IP" || { printf 'Author: 2025ae05142 LoadBalancer IP not assigned\n' >&2; exit 1; }
SERVICE_URL="http://$LB_IP"
printf 'SERVICE_URL=%s\n' "$SERVICE_URL"
```

Use the printed address as `SERVICE_URL`, then verify both endpoints:

```sh
curl --fail-with-body --silent --show-error --noproxy '*' "$SERVICE_URL/health"
curl --fail-with-body --silent --show-error --noproxy '*' \
  -H 'Content-Type: application/json' \
  --data-binary @examples/patient.json "$SERVICE_URL/predict"
```

These addresses are local to the VM, not public endpoints. Stop the tunnel with
Ctrl-C in its terminal after all local testing/recording is finished; subsequent
LoadBalancer access requires restarting it. For the retained NodePort route,
use `minikube service heart-disease-api -p heart-disease -n heart-disease --url`.

The recorded command output and sample response, including the historical
NodePort-only deployment, are in [deploy_smoke.md](./deploy_smoke.md).

## Monitoring and logging

Author: `2025ae05142`

### Current evidence

Use the [restored monitoring verification](#restored-monitoring-verification-2026-10-19),
[current Grafana capture](../screenshots/phase-8-restored-grafana.png), and
[current metrics capture](../screenshots/phase-8-restored-metrics.png) for the
report and demonstration. Earlier captures below are retained as historical
evidence, not evidence of the restored cluster's state.

### Deployment and access

Validated on the BITS Prayogshala Linux VM as `s2025ae05142`, in the
`heart-disease` Minikube cluster. The instrumented API image is
`heart-disease-2025ae05142:phase8-review`; Prometheus uses `prom/prometheus:v2.55.1`
and Grafana uses `grafana/grafana:11.4.0`. The API remains available through
the retained NodePort at `http://192.168.49.2:30080` and the corrected
LoadBalancer route described in [DEPLOY.md](./DEPLOY.md). On the restored VM,
the LoadBalancer address is `http://10.97.154.192` while `minikube tunnel`
is running. Addresses may change when the cluster is recreated.

The monitoring Services are ClusterIP-only. To access their UIs from the VM,
run each command in a separate terminal and keep the port-forward running:

```sh
minikube kubectl -p heart-disease -- port-forward --address=127.0.0.1 \
  service/prometheus 19090:9090 -n heart-disease
minikube kubectl -p heart-disease -- port-forward --address=127.0.0.1 \
  service/grafana 13000:3000 -n heart-disease
```

Grafana's admin password is held only in the Kubernetes Secret
`grafana-admin`; it is not stored in this repository. Anonymous access is
read-only. Do not publish the port-forward or commit the Secret.

### Telemetry contract

- Each `POST /predict` emits one JSON log event with author, UTC timestamp,
  feature names only, prediction, confidence, and latency in milliseconds.
  Invalid feature requests are logged with null prediction/confidence. Missing
  or malformed JSON bodies are handled before the endpoint and are also logged
  once with empty feature names and null prediction/confidence; values from the
  request body are not logged.
- `GET /metrics` exposes
  `heart_disease_prediction_requests_total` and the
  `heart_disease_prediction_request_duration_seconds` histogram. The metrics
  have no patient data or request-specific labels.
- Prometheus scrapes
  `heart-disease-api.heart-disease.svc.cluster.local:80/metrics` every 15
  seconds. The provisioned Grafana dashboard shows request rate, p50/p95
  latency, and total request count.

### Historical live smoke evidence

The API health endpoint returned:

```sh
curl --fail-with-body --silent --show-error \
  http://192.168.49.2:30080/health
```

```json
{"status":"ok"}
```

A real sample request used the repository's feature-only sample body:

```sh
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @examples/patient.json \
  http://192.168.49.2:30080/predict
```

```json
[{"prediction":0,"confidence":0.7466949562461239}]
```

Five further valid requests and one invalid `{}` request returned five HTTP
200 responses and one HTTP 422. The API pod log contained seven JSON events
for the seven total requests (six successful, one invalid), each with exactly
the documented fields and author tag; the invalid event had null prediction
and confidence. The logged feature field contained names only. Automated API
tests additionally exercise malformed JSON and a missing body, confirming each
gets one event, one request-counter increment, and one histogram observation.

After Prometheus's next 15-second scrape, its active target reported `health:
up` with an empty `lastError`. Querying
`heart_disease_prediction_requests_total` returned `7`; the API's live
histogram also reported count `7`. Grafana `/api/health` returned database
`ok`, version `11.4.0`; the provisioned dashboard was searchable as
`heart-disease-api`.

The screenshot was taken from the live Grafana UI after all three panels had
rendered and showed total request count `7`:

![Historical Grafana request and latency dashboard](../screenshots/phase-8-grafana-dashboard.png)

The review-correction request cases were also exercised against the live VM
API in Swagger UI (valid and malformed JSON) and a browser form that submitted
an actually empty body. Each request incremented the API counter exactly once:

- [Valid prediction: HTTP 200 and response](../screenshots/phase-8-valid-request.png)
- [Malformed JSON: HTTP 422 validation response](../screenshots/phase-8-malformed-json.png)
- [Missing request body: live server validation response](../screenshots/phase-8-missing-body.png)

### Restored monitoring verification (2026-10-19)

Author: `2025ae05142`

Following cluster recreation and the LoadBalancer correction, the existing
monitoring configuration and workloads were restored on VM
`ip-10-3-23-253.ap-south-1.compute.internal` as `s2025ae05142`. No API code,
dashboard queries, image tags, or scrape address needed to change: Prometheus
still reaches the API through its internal Service DNS name.

Before restoration, `free -h` reported 15 GiB total and 11 GiB available.
Created the four ConfigMaps from the checked-in monitoring files and generated
a new random Grafana admin password directly into a Kubernetes Secret via
standard input; no password was printed or written into the repository.
Applied `k8s/monitoring.yaml` and waited for both deployments:

```sh
minikube kubectl -p heart-disease -- apply -f k8s/monitoring.yaml
minikube kubectl -p heart-disease -- rollout status deployment/prometheus \
  -n heart-disease --timeout=180s
minikube kubectl -p heart-disease -- rollout status deployment/grafana \
  -n heart-disease --timeout=180s
minikube kubectl -p heart-disease -- get pods,svc -n heart-disease
```

Both rollouts passed. API, Prometheus, and Grafana were each `1/1 Running` with
zero restarts. Monitoring Services remain ClusterIP; only the API uses
LoadBalancer. Loopback port-forwards at `19090` and `13000` were started using
the commands above and verified responsive.

Actual HTTP checks through `http://10.97.154.192` and JSON assertions verified:

- A valid sample returned HTTP 200 and the expected prediction/confidence.
  Malformed JSON and a missing body each returned HTTP 422.
- Counter and histogram count both increased from `8` to `11` across those
  three requests. The latest three JSON log events had author `2025ae05142`;
  rejected-body events had empty feature names and null prediction/confidence.
- Prometheus reported the API target `up`, empty `lastError`, and counter `11`
  after its scrape. Request-rate and p95 histogram queries returned finite
  numeric values. Grafana reported database `ok`, version `11.4.0`, and its
  provisioned dashboard contained all three panels.
- A separate terminal-capture request increased the counter and histogram
  from `11` to `12`. These are cumulative counts from this restored API
  process; they need not equal the earlier historical screenshot's count.

The fresh browser capture shows all three rendered panels with real data and
total count `11`, taken before the additional terminal-capture request:

![Restored live Grafana dashboard](../screenshots/phase-8-restored-grafana.png)

[Restored metrics and workload evidence](../screenshots/phase-8-restored-metrics.png)
shows the ready workloads, counter/histogram increment from `11` to `12`,
prediction response, Grafana health, and Prometheus target status. Both PNGs
were visually inspected. The integrated browser required Dev Tunnels sign-in,
so capture used an isolated Firefox window directly on the VM's localhost;
no tunnel access controls were changed.

Temporary screenshot terminal/browser processes were closed. The Minikube
LoadBalancer tunnel and loopback monitoring port-forwards remain running for
student review and recording preparation. Node capacity/resource allocations
were inspected; scheduled requests total 1,050m CPU/938Mi memory, and limits
total 3 CPUs/2,730Mi. No model training, CI execution, commit, push, or video
recording occurred during this restoration.

### Historical resource gate

#### Review-correction verification

The corrected image was built as
`heart-disease-2025ae05142:phase8-review` (image ID
`sha256:427cfad548db527c26ed9b20d82e9427b51dad5404efb695f2e15a02b4fce92b`)
and rolled out to the VM's Minikube Deployment. Through the NodePort, a
successful sample returned HTTP 200, malformed JSON returned HTTP 422, and a
missing body returned HTTP 422. Across those three requests, the API counter
and histogram count each increased from 0 to 3. The API pod emitted exactly
three JSON lines: one prediction event and two rejected-body events with empty
feature lists and null prediction/confidence. After the next scrape,
Prometheus reported the API target `up`, no scrape error, and request counter
`3`.

At validation, `free -h` reported 15 GiB total and 9.8 GiB available on the VM.
The Minikube node had 4 CPUs and 15,968,384 KiB memory. `kubectl describe
node heart-disease` reported total workload requests of 1,050m CPU and 938Mi
memory (26% and 6% of node capacity); limits were 3 CPUs and 2,730Mi. The
Prometheus and Grafana pods each request 100m CPU/256Mi and are limited to 1
CPU/768Mi. Both use ephemeral storage with explicit size limits.

The `kubectl top nodes` Metrics API was unavailable, so no live usage figure
from that API is claimed. Capacity and scheduled requests were verified with
`free -h` and `minikube kubectl -p heart-disease -- describe node heart-disease`.

### Reproduction outline

Run on the VM from the repository root. Generate the locally ignored model
artifact before building the image. Create/update the ConfigMaps from the
checked-in monitoring files, ensure the `grafana-admin` Secret exists without
placing its password in source control, and then apply the workloads:

```sh
.venv-phase4/bin/python -m src.train.package
docker build --tag heart-disease-2025ae05142:phase8-review .
minikube image load --profile=heart-disease heart-disease-2025ae05142:phase8-review
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
minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/monitoring.yaml
minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api \
  -n heart-disease --timeout=180s
minikube kubectl -p heart-disease -- rollout status deployment/prometheus \
  -n heart-disease --timeout=180s
minikube kubectl -p heart-disease -- rollout status deployment/grafana \
  -n heart-disease --timeout=180s
```

At validation, all three pods were `1/1 Running` with zero restarts. The API
was rebuilt with the Phase 8 tag and successfully rolled out. A controlled
Grafana restart briefly invalidated its existing port-forward; the forward
was re-established and the dashboard recaptured after Grafana returned
healthy. Final lint and test checks are recorded in
[phase progress](./PROGRESS.md).
