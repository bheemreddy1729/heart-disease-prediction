# Model comparison — Author: `2025ae05142`

- Validation: 5-fold stratified cross-validation (shuffle, `random_state=42`).
- Scores are mean ± sample standard deviation across folds.
- Champion rule: highest mean recall, then ROC-AUC, then precision; accuracy is reported but is not the selection criterion.
- Selected champion: **rbf_svc**.

| Model | Accuracy | Precision | Recall | ROC-AUC |
|---|---:|---:|---:|---:|
| logistic_regression | 0.855 ± 0.054 | 0.874 ± 0.064 | 0.798 ± 0.081 | 0.919 ± 0.023 |
| random_forest | 0.838 ± 0.031 | 0.851 ± 0.061 | 0.791 ± 0.031 | 0.914 ± 0.025 |
| rbf_svc | 0.845 ± 0.051 | 0.850 ± 0.067 | 0.806 ± 0.066 | 0.902 ± 0.032 |

Cross-validation scores estimate performance on held-out folds; they are not a claim of clinical readiness.
