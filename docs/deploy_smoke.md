# Container and Kubernetes smoke evidence

Author: `2025ae05142`

## Current evidence

Use the [LoadBalancer correction](#loadbalancer-correction-2026-10-19),
[current deployment capture](../screenshots/phase-7-loadbalancer.png), and
[current tunnel capture](../screenshots/phase-7-loadbalancer-tunnel.png) for
the report and demonstration. The NodePort-only results below are retained
as historical evidence and do not establish the PDF's exposure requirement.

## Historical NodePort execution environment

- Host: BITS Prayogshala Linux VM (`ip-10-3-16-15.ap-south-1.compute.internal`)
- User: `s2025ae05142`
- Home: `/home/s2025ae05142`
- Repository: `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`
- Minikube: `v1.35.0`, Docker driver
- Kubernetes: `v1.32.0`
- Client: Minikube-bundled `kubectl` v1.32.0; standalone `kubectl` is not installed.

## Cluster and deployment

Started a single-node local cluster:

```sh
minikube start -p heart-disease --driver=docker --cpus=2 --memory=4096 --disk-size=20g
```

Loaded the already-built local serving image; this requires no registry:

```sh
minikube image load --profile=heart-disease heart-disease-2025ae05142:phase6
```

Applied the manifests and waited for the deployment:

```sh
minikube kubectl -p heart-disease -- apply -f k8s/namespace.yaml
minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/service.yaml
minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api \
  -n heart-disease --timeout=180s
```

Result: namespace, Deployment, and Service created; rollout completed
successfully. After the required Service-type correction,
`get pods,deployments,services,endpoints -n heart-disease` reported:

```text
deployment.apps/heart-disease-api   1/1   1   1
service/heart-disease-api           NodePort   10.102.76.112   <none>   80:30080/TCP
endpoints/heart-disease-api         10.244.0.3:8000
pod/heart-disease-api-745b445899-b5rgd   1/1   Running   0
```

`describe pod` confirmed image `heart-disease-2025ae05142:phase6` with image
ID `sha256:b6ef0aa7a8454109bdb78c96b3fc91aef71a7ccd559f85189d311305d831105f`,
UID 10001, read-only root filesystem, readiness and liveness probes on
`/health`, requests of 100m CPU/256Mi memory, and limits of 1 CPU/1Gi memory.

## NodePort Service verification

The initial deployment used NodePort `30080`. Primary-PDF review later
established that the assignment requires Load Balancer or Ingress exposure;
these NodePort results prove connectivity, not compliance with that requirement.
The LoadBalancer correction below supersedes the initial exposure design.
The original check obtained the URL from Minikube:

```sh
SERVICE_URL=$(minikube service heart-disease-api -p heart-disease -n heart-disease --url)
printf 'SERVICE_URL=%s\n' "$SERVICE_URL"
```

Command output:

```text
http://192.168.49.2:30080
```

Health check:

```sh
curl --fail-with-body --silent --show-error http://192.168.49.2:30080/health
```

Response:

```json
{"status":"ok"}
```

Prediction request:

```sh
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @examples/patient.json \
  http://192.168.49.2:30080/predict
```

Response:

```json
[{"prediction":0,"confidence":0.7466949562461239}]
```

The pod logs showed successful `/health` probe requests and the API started
without restarts. The Minikube node address and NodePort are local to the VM;
the Minikube cluster and Deployment remain running for the next phase.

## Historical NodePort screenshot

- [Historical NodePort workload and live Minikube Service prediction](../screenshots/phase-7-kubernetes.png)

## LoadBalancer correction (2026-10-19)

Author: `2025ae05142`

### Current VM and restoration

- Host: `ip-10-3-23-253.ap-south-1.compute.internal`; user `s2025ae05142`;
  home `/home/s2025ae05142`.
- The initial `minikube status -p heart-disease` reported
  `Profile "heart-disease" not found`. The subsequent profile listing reported
  `MK_USAGE_NO_PROFILE: No minikube profile was found`. Docker was available,
  but there were no project images. Historical cluster state was not assumed.
- The retained model and dataset hashes matched their provenance. Python and
  all recorded library versions matched; local sample inference succeeded.
  No retraining or new MLflow runs were needed.
- Rebuilt `heart-disease-2025ae05142:phase8-review`; image ID
  `sha256:43b07d94fa328b9aa19a5c2fc88af9b2daf072713659b4cfe8ddd7f7a482b6d0`.
  A temporary loopback-only container returned health and the expected sample
  prediction as UID 10001, then was stopped and removed. The first smoke
  attempt encountered a startup `ConnectionResetError`; explicit readiness
  retries resolved it, and the repeat smoke test passed.

Recreated the cluster, loaded the image, and applied the existing manifests:

```sh
minikube start -p heart-disease --driver=docker --cpus=2 --memory=4096 --disk-size=20g
minikube image load --profile=heart-disease heart-disease-2025ae05142:phase8-review
minikube kubectl -p heart-disease -- apply -f k8s/namespace.yaml
minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/service.yaml
minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api \
  -n heart-disease --timeout=180s
```

Cluster creation and rollout succeeded; Kubernetes v1.32.0 node `heart-disease`
was Ready and API readiness `/readyz` returned `ok`.

### LoadBalancer verification

Changed `k8s/service.yaml` to `type: LoadBalancer`, retaining nodePort `30080`.
Server-side dry run and apply both succeeded:

```sh
minikube kubectl -p heart-disease -- apply --dry-run=server -f k8s/service.yaml
minikube kubectl -p heart-disease -- apply -f k8s/service.yaml
minikube tunnel -p heart-disease
```

The tunnel remained running, reporting route `10.96.0.0/12 -> 192.168.49.2`,
service `heart-disease-api`, and no Minikube, router, or loadbalancer-emulator
errors. No Ingress controller was installed.

`minikube kubectl -p heart-disease -- get service heart-disease-api -n
heart-disease -o wide` and `get pods -n heart-disease` returned:

```text
NAME                TYPE           CLUSTER-IP      EXTERNAL-IP     PORT(S)
heart-disease-api   LoadBalancer   10.97.154.192   10.97.154.192   80:30080/TCP

NAME                                 READY   STATUS    RESTARTS
heart-disease-api-7778d56bf4-4w72w   1/1     Running   0
```

A Python HTTP client with proxies disabled made actual requests to the assigned
LoadBalancer address, asserting both decoded responses:

```text
Author: 2025ae05142 LoadBalancer URL: http://10.97.154.192
Author: 2025ae05142 health: {'status': 'ok'}
Author: 2025ae05142 prediction: [{'prediction': 0, 'confidence': 0.7466949562461239}]
```

The following curl commands were also executed successfully, returning
`{"status":"ok"}` and the same prediction/confidence JSON:

```sh
curl --fail-with-body --silent --show-error --noproxy '*' \
  http://10.97.154.192/health
curl --fail-with-body --silent --show-error --noproxy '*' \
  -H 'Content-Type: application/json' --data-binary @examples/patient.json \
  http://10.97.154.192/predict
```

The retained NodePort health/prediction curl checks also passed, and API logs
contained the attributed prediction events. The tunnel and cluster remain
running for student review; their addresses are local to the VM. Monitoring
workloads were not restored in this step. The earlier screenshot is historical
NodePort evidence; current LoadBalancer captures are linked below.

### Verified LoadBalancer screenshots

Captured from actual VM terminal execution at the student's request, then
visually inspected for readable commands and results:

- [Live deployment and endpoint checks](../screenshots/phase-7-loadbalancer.png):
  VM identity, running cluster, pod 1/1 Running with zero restarts,
  LoadBalancer external IP, health response, and sample prediction.
- [Tunnel and prediction evidence](../screenshots/phase-7-loadbalancer-tunnel.png):
  actual tunnel process, local network route, LoadBalancer Service, sample
  request, successful curl response, and attributed request logs.

The terminal capture helpers were closed afterward; the existing tunnel
continues running for VM-local access. No screenshot shows a public endpoint.

## Docker container smoke evidence

Author: `2025ae05142`

### Execution environment

- Host: BITS Prayogshala Linux VM
- User: `s2025ae05142`
- Home: `/home/s2025ae05142`
- Repository: `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`
- Docker Engine: `28.0.1`

### Prerequisite and image

The serving image requires the locally generated, gitignored
`models/heart_pipeline.joblib`; it is intentionally not tracked or committed.
At validation, the packaged artifact SHA-256 was
`e9e7aee665648300c2eac5a917cca89a2c401f9c32a881a65e5c20df99d0fc4c`.
Confirmed ignored and untracked with `git check-ignore -v
models/heart_pipeline.joblib` and `git ls-files --error-unmatch
models/heart_pipeline.joblib` (the latter correctly returned nonzero).

Build:

```sh
docker build --tag heart-disease-2025ae05142:phase6 .
```

Result: successful; image ID
`sha256:b6ef0aa7a8454109bdb78c96b3fc91aef71a7ccd559f85189d311305d831105f`.

Run the API bound only to VM loopback:

```sh
docker run --detach --name heart-disease-phase6-review \
  --publish 127.0.0.1:8000:8000 heart-disease-2025ae05142:phase6
```

Container ID began `e47a5fbd5333`. `docker exec
heart-disease-phase6-review id` returned:

```text
uid=10001(app) gid=10001(app) groups=10001(app)
```

### Endpoint checks

Health command:

```sh
curl --fail-with-body --silent --show-error --retry 30 --retry-delay 1 \
  --retry-connrefused http://127.0.0.1:8000/health
```

Response:

```json
{"status":"ok"}
```

Sample prediction request body (`examples/patient.json`):

```json
[
  {
    "age": 63,
    "sex": 1,
    "cp": 1,
    "trestbps": 145,
    "chol": 233,
    "fbs": 1,
    "restecg": 2,
    "thalach": 150,
    "exang": 0,
    "oldpeak": 2.3,
    "slope": 3,
    "ca": 0,
    "thal": 6
  }
]
```

Prediction command:

```sh
curl --fail-with-body --silent --show-error --retry 30 --retry-delay 1 \
  --retry-connrefused -H 'Content-Type: application/json' \
  --data-binary @examples/patient.json http://127.0.0.1:8000/predict
```

Response:

```json
[{"prediction":0,"confidence":0.7466949562461239}]
```

The container reported `state=running user=app`. The smoke-test container was
stopped and removed after verification and screenshot capture. No Kubernetes
deployment was started.

### Screenshots

- [Live health endpoint and non-root container check](../screenshots/phase-6-health.png)
- [Live sample request body and prediction response](../screenshots/phase-6-predict.png)
- [Docker image tag, ID, and size](../screenshots/phase-6-docker-image.png)
- [Running container, published port, CPU/memory usage, and health](../screenshots/phase-6-docker-container.png)

The Docker usage capture showed image tag `heart-disease-2025ae05142:phase6`
(469 MB; 469,190,217 bytes reported by inspect) and a running container with
loopback-only port publishing, non-root `app` user, and approximately 122 MiB
memory use at capture time. Resource usage is a point-in-time observation and
varies with host activity.
