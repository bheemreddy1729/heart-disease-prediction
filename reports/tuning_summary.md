# RBF SVC tuning summary - Author: `2025ae05142`

- Experiment: `heart-disease-tuning-2025ae05142`; tracking URI: `sqlite:////home/s2025ae05142/workspace/Assignment-I/heart-disease-prediction/mlflow.db`.
- Dataset SHA-256: `655b46ed75efcb7eb0f636b952f6ed68c6bf48487c6dbde7070ade6a3d5390d8`.
- Validation: 5 shuffled stratified folds, seed 42.
- Reuses fold-local imputation, scaling, and encoding from baseline training.
- Ranking: mean recall, then ROC-AUC, then precision; exact ties retain grid order.
- Baseline: `C=1,gamma=scale`; selected tuning configuration: `C=1,gamma=0.1`.
- Scores are fold means +/- sample standard deviations, not independent test scores.

| Configuration | Accuracy | Precision | Recall | ROC-AUC | MLflow run ID |
|---|---:|---:|---:|---:|---|
| C=0.1,gamma=scale | 0.835082 +/- 0.044515 | 0.854190 +/- 0.067101 | 0.777513 +/- 0.091344 | 0.904375 +/- 0.035896 | `38982d32e6284809a070768a67595f95` |
| C=0.1,gamma=0.01 | 0.729454 +/- 0.023709 | 0.967532 +/- 0.044988 | 0.424603 +/- 0.040468 | 0.901249 +/- 0.028263 | `a83fdba183f144f39220f1c580ede1ad` |
| C=0.1,gamma=0.1 | 0.835082 +/- 0.044515 | 0.854190 +/- 0.067101 | 0.777513 +/- 0.091344 | 0.904165 +/- 0.036188 | `ff2bf18ef212421e90be8751eaa0bd73` |
| C=1,gamma=scale | 0.844754 +/- 0.050633 | 0.850069 +/- 0.066625 | 0.805556 +/- 0.065626 | 0.902143 +/- 0.031940 | `d1f038a9a8d34431a631f9ccb582cbd6` |
| C=1,gamma=0.01 | 0.854699 +/- 0.048971 | 0.874300 +/- 0.052522 | 0.797884 +/- 0.095652 | 0.916156 +/- 0.020382 | `56c8636e153e4eada9b23368cc90e1d5` |
| C=1,gamma=0.1 | 0.848033 +/- 0.046294 | 0.851656 +/- 0.064534 | 0.812698 +/- 0.059748 | 0.901927 +/- 0.032086 | `05e2a3643a7444788a4945f2e8d6b9ad` |
| C=10,gamma=scale | 0.805082 +/- 0.062715 | 0.801749 +/- 0.089177 | 0.776455 +/- 0.104027 | 0.870753 +/- 0.038532 | `8df7afe5e52747a79f88f45839c6d0e3` |
| C=10,gamma=0.01 | 0.847923 +/- 0.058552 | 0.865056 +/- 0.063043 | 0.790476 +/- 0.089325 | 0.914393 +/- 0.022262 | `bc6a4e2e3bc14988b482951e96b0ee3f` |
| C=10,gamma=0.1 | 0.795246 +/- 0.050795 | 0.789171 +/- 0.083102 | 0.769312 +/- 0.094859 | 0.869868 +/- 0.037943 | `8f47ad1653044c0d827a69300975bf90` |

## Selected configuration minus original baseline (CV mean differences)

- accuracy: +0.003279
- precision: +0.001587
- recall: +0.007143
- roc_auc: -0.000216

The same dataset was used for original candidate selection and tuning. These differences are selection results, not proof of generalization improvement or clinical validation. The grid does not establish a global optimum.

Each run records parameters, metrics, configuration scores, a comparison plot, and this summary. No registered model or serving artifact is changed. The deployed calibrated baseline remains unchanged pending an explicit promotion decision.

Reproduce on the VM: `.venv/bin/python -m src.train.tune`. This appends tuning runs and updates only this tuning summary.
