# Kubernetes deployment

Author: `2025ae05142`

This project deploys its local Phase 6 image to Minikube with the Docker
driver. The `heart-disease-api` Service is a `NodePort` on port `30080`, as
required by the assignment. Use `minikube service --url` to obtain the node
address and port to use with curl. No cloud account or public registry is
required.

```sh
minikube start -p heart-disease --driver=docker --cpus=2 --memory=4096 --disk-size=20g
minikube image load --profile=heart-disease heart-disease-2025ae05142:phase6
minikube kubectl -p heart-disease -- apply -f k8s/namespace.yaml
minikube kubectl -p heart-disease -- apply -f k8s/deployment.yaml -f k8s/service.yaml
minikube kubectl -p heart-disease -- rollout status deployment/heart-disease-api \
  -n heart-disease --timeout=180s
minikube kubectl -p heart-disease -- get pods,services -n heart-disease
SERVICE_URL=$(minikube service heart-disease-api -p heart-disease -n heart-disease --url)
printf 'SERVICE_URL=%s\n' "$SERVICE_URL"
```

Use the printed address as `SERVICE_URL`, then verify both endpoints:

```sh
curl --fail-with-body --silent --show-error "$SERVICE_URL/health"
curl --fail-with-body --silent --show-error \
  -H 'Content-Type: application/json' \
  --data-binary @examples/patient.json "$SERVICE_URL/predict"
```

The recorded command output and sample response are in
[deploy_smoke.md](./deploy_smoke.md).
