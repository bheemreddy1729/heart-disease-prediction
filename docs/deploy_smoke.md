# Kubernetes deployment smoke test

Author: `2025ae05142`

## Execution environment

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

The assignment requires a `NodePort` or `LoadBalancer` Service. This deployment
uses NodePort `30080`. Obtain the URL from Minikube and use it directly:

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

## Screenshot

- [NodePort workload and live Minikube Service prediction](../screenshots/phase-7-kubernetes.png)
