# Project decisions

Author: `2025ae05142`

Decisions are recorded as each phase reaches its design gate. Do not substitute third-party student implementations for original project work.

## Phase 0

- **Runtime:** Use the BITS Prayogshala Linux VM and its detected user home, `/home/s2025ae05142`. Do not assume a cloud account or move implementation to the Windows laptop.
- **Stack:** Retain the assignment's Python, pandas, scikit-learn, MLflow, FastAPI, pytest, ruff, Docker, GitHub Actions, Minikube, and Prometheus-client stack. The VM has Python 3.12.9, Docker 28.0.1, and Minikube 1.35.0. Reassess individual components only if a concrete compatibility probe fails.
- **Tracking and artifacts:** Use a local SQLite MLflow backend and local file artifacts, as required; do not introduce hosted tracking.
- **Data and target:** Use the UCI Heart Disease processed Cleveland dataset (dataset 45). Treat target value 0 as absence and values 1–4 as presence.
- **Leakage prevention:** Any model imputers, encoders, and scalers must be fit as part of the training pipeline, within training folds where cross-validation is used.
- **Run attribution:** Tag each MLflow run, log line, and report header with `2025ae05142`.
- **Cluster and CI:** Target local Minikube on the assigned VM to keep deployment reproducible without requiring a public-cloud account. The repository's Actions API is reachable, but workflow execution remains unverified until Phase 5; do not push or trigger a workflow unless explicitly requested.
- **Deferred decisions:** EDA missing-value display/handling, the third classifier, the random seed, champion selection rule, and serving/deployment details will be decided and justified in their relevant phases.

## Phase 1

- **EDA missingness:** Preserve source `?` values as missing in the processed table, report missing counts, and do not drop rows or impute during EDA. This keeps all 303 records available and avoids fitting imputation statistics before the training split. Histograms omit missing values within each feature; the correlation matrix uses pairwise complete observations. Fit any later imputer only on training data as part of the model pipeline.
- **Target:** Map original Cleveland `num=0` to absence (`0`) and `num=1,2,3,4` to presence (`1`); reject target values outside this defined domain.
- **EDA scope:** Plot histograms for the 13 numeric clinical features (not the outcome), use Pearson correlations across those features, and show class counts after binarization.
- **Reproducibility:** Download the processed Cleveland file from the UCI URL documented in `docs/DATA.md`; retain its local raw copy and record its download date. Pin only the pandas and matplotlib dependencies needed by this phase; extend the manifest when later phases need their dependencies.
- **Alternatives considered:** Dropping incomplete patient rows would discard six otherwise usable records; imputing now would estimate values before a train/test split. Retaining missing cells and reporting per-column counts preserves source evidence without leakage; modeling-time imputation remains for the training pipeline. Plotting targets among the clinical-feature histograms would mix outcome and predictor distributions, so the target is instead shown separately in the class-balance chart. The source is the UCI repository rather than a repackaged dataset so the download remains traceable to the assigned dataset.

## Phase 2

- **Candidate algorithms:** Compare Logistic Regression, Random Forest, and RBF-kernel Support Vector Classification (SVC). Logistic Regression provides a regularized linear baseline; Random Forest can model nonlinear splits and interactions; RBF SVC tests a smooth nonlinear boundary on this small tabular dataset. These give a linear baseline and two distinct nonlinear alternatives, as required, without assuming one family will win. No external implementation is copied; use the official scikit-learn estimator APIs.
- **Feature preprocessing:** Treat `age`, `trestbps`, `chol`, `thalach`, and `oldpeak` as continuous numeric measurements; median-impute within a fold and standardize them. Treat `sex`, `cp`, `fbs`, `restecg`, `exang`, `slope`, `ca`, and `thal` as coded categorical values; impute the most frequent value within a fold and one-hot encode with unknown categories ignored. This avoids imposing artificial distances/order on nominal clinical codes and keeps inference preprocessing inside the fitted pipeline. The target `num` is excluded from features.
- **Validation:** Use five-fold stratified cross-validation, shuffled with fixed `random_state=42`, for every candidate; return accuracy, precision, recall, and ROC-AUC as fold means and standard deviations. Shuffling with a recorded seed provides repeatable, class-preserving partitions; five folds retain a useful validation set size for the 303-row dataset.
- **Champion rule:** Maximize mean recall first because missed positive disease cases are the most costly screening error; break recall ties by mean ROC-AUC (ranking/discrimination), then mean precision. Report accuracy too, but do not select on accuracy alone. This is a model-comparison rule for this assignment, not a clinical deployment claim.
- **Alternatives considered:** A single train/test split would make model ranking depend heavily on one small sample; stratified folds use the limited data more efficiently while preserving both classes. Standardizing all numeric codes would falsely treat nominal categories as equally spaced measurements; one-hot encoding avoids that. Selecting by accuracy alone can obscure false negatives, so recall is primary and ROC-AUC and precision are tie-breakers. The scikit-learn `Pipeline`, `ColumnTransformer`, `StratifiedKFold`, and `cross_validate` interfaces guide the implementation; see the official [compose API](https://scikit-learn.org/stable/modules/compose.html), [cross-validation API](https://scikit-learn.org/stable/modules/cross_validation.html), and [metrics API](https://scikit-learn.org/stable/modules/model_evaluation.html).
