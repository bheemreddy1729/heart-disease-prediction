# Docker smoke test

Author: `2025ae05142`

## Execution environment

- Host: BITS Prayogshala Linux VM
- User: `s2025ae05142`
- Home: `/home/s2025ae05142`
- Repository: `/home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction`
- Docker Engine: `28.0.1`

## Prerequisite and image

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

## Endpoint checks

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

## Screenshots

- [Live health endpoint and non-root container check](../screenshots/phase-6-health.png)
- [Live sample request body and prediction response](../screenshots/phase-6-predict.png)
- [Docker image tag, ID, and size](../screenshots/phase-6-docker-image.png)
- [Running container, published port, CPU/memory usage, and health](../screenshots/phase-6-docker-container.png)

The Docker usage capture showed image tag `heart-disease-2025ae05142:phase6`
(469 MB; 469,190,217 bytes reported by inspect) and a running container with
loopback-only port publishing, non-root `app` user, and approximately 122 MiB
memory use at capture time. Resource usage is a point-in-time observation and
varies with host activity.
