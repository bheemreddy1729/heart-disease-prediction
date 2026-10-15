# Model comparison — Author: `2025ae05142`

- Validation: 5-fold stratified cross-validation (shuffle, `random_state=42`).
- Scores are mean ± sample standard deviation across folds.
- Champion rule: highest mean recall, then ROC-AUC, then precision; accuracy is reported but is not the selection criterion.
- Selected champion: **rbf_svc**.

| Model | Accuracy | Precision | Recall | ROC-AUC |
|---|---:|---:|---:|---:|
| logistic_regression | 0.8547 ± 0.0542 | 0.8744 ± 0.0640 | 0.7979 ± 0.0812 | 0.9188 ± 0.0232 |
| random_forest | 0.8384 ± 0.0310 | 0.8505 ± 0.0612 | 0.7913 ± 0.0306 | 0.9144 ± 0.0255 |
| rbf_svc | 0.8448 ± 0.0506 | 0.8501 ± 0.0666 | 0.8056 ± 0.0656 | 0.9021 ± 0.0319 |

Cross-validation scores estimate performance on held-out folds; they are not a claim of clinical readiness.
