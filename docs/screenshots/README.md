# Screenshot checklist

Author: `2025ae05142`

The evidence screenshots already captured for this project are stored in the
repository-level [`screenshots/`](../../screenshots/) folder; the data figures
are under [`reports/figures/`](../../reports/figures/). Use the genuine
captures listed below where they meet the submission requirement. Capture any
remaining evidence from the actual VM or application UI. Do not recreate,
retouch, or invent command output, CI status, predictions, or dashboard values.

| Evidence to include | Existing evidence | Remaining capture/action |
|---|---|---|
| EDA figures: feature distributions, class balance, and correlations | [Feature histograms](../../reports/figures/feature_histograms.png), [class balance](../../reports/figures/class_balance.png), and [correlation heatmap](../../reports/figures/correlation_heatmap.png) | Already generated from the project data. Include these figures in the report/submission. |
| MLflow candidate runs and registry | [Experiment runs](../../screenshots/phase-3-mlflow-experiment.png), [champion run](../../screenshots/phase-3-mlflow-champion-run.png), [registry](../../screenshots/phase-3-mlflow-registry.png), and [artifacts](../../screenshots/phase-3-mlflow-artifacts.png) | Captures exist; confirm they are legible in the submitted report pack. |
| GitHub Actions green workflow and failure-then-recovery proof | [Hosted run](../../screenshots/phase-5-actions-run.png), [deliberate failure](../../screenshots/phase-5-deliberate-failure.png), [green after revert](../../screenshots/phase-5-reverted-success.png), and [training evidence](../../screenshots/phase-5-training-evidence.png) | The screenshots show the Phase 5 workflow. The later [verified green Phase 8 run](https://github.com/bheemreddy1729/heart-disease-prediction/actions/runs/38955767909) is verified in GitHub and [progress evidence](../PROGRESS.md); capture that current run in the GitHub UI too if the submission needs a screenshot of the latest green run. |
| Docker build, running container, and curl response | [Built image](../../screenshots/phase-6-docker-image.png), [running container](../../screenshots/phase-6-docker-container.png), [health and non-root check](../../screenshots/phase-6-health.png), and [prediction request/response](../../screenshots/phase-6-predict.png) | Captures exist; see the [Docker smoke record](../deploy_smoke.md#docker-container-smoke-evidence). |
| Kubernetes workload status and live prediction | [LoadBalancer, ready pod, and endpoint responses](../../screenshots/phase-7-loadbalancer.png), [tunnel, route, request, and logs](../../screenshots/phase-7-loadbalancer-tunnel.png); [historical NodePort evidence](../../screenshots/phase-7-kubernetes.png) | LoadBalancer captures were taken from actual VM terminal execution at the student's request and visually verified. They show the corrected exposure and successful curl prediction. An in-cluster curl is not explicitly required by the assignment PDF. See the [deployment smoke record](../deploy_smoke.md). |
| Metrics or Grafana | [Restored Grafana dashboard](../../screenshots/phase-8-restored-grafana.png), [restored workloads and metrics increment](../../screenshots/phase-8-restored-metrics.png); [historical dashboard](../../screenshots/phase-8-grafana-dashboard.png) | Fresh genuine captures were visually verified after LoadBalancer restoration. Dashboard count 11 precedes the terminal request that increased counts to 12. |
| Phase 8 request outcomes | [Valid request](../../screenshots/phase-8-valid-request.png), [malformed JSON](../../screenshots/phase-8-malformed-json.png), and [missing body](../../screenshots/phase-8-missing-body.png) | These actual UI responses are additional monitoring/API validation evidence. |

Before submission, verify that each selected image is readable at the intended
document size and that any newly captured screenshot shows the real command or
application state. Keep this file as the checklist; do not copy screenshot
files into this directory.
