"""Compare heart-disease classifiers with leakage-safe stratified cross-validation."""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
from pathlib import Path

import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "heart.csv"
REPORT_PATH = ROOT / "reports" / "model_comparison.md"
TRACKING_URI = f"sqlite:///{ROOT / 'mlflow.db'}"
ARTIFACT_ROOT = ROOT / "mlruns"
EXPERIMENT_NAME = "heart-disease-2025ae05142"
REGISTERED_MODEL_NAME = "heart-disease-champion-2025ae05142"
MLFLOW_SUMMARY_PATH = ROOT / "reports" / "mlflow_summary.md"
AUTHOR = "2025ae05142"
TARGET = "num"
RANDOM_STATE = 42
N_SPLITS = 5

NUMERIC_FEATURES = ["age", "trestbps", "chol", "thalach", "oldpeak"]
CATEGORICAL_FEATURES = [
    "sex",
    "cp",
    "fbs",
    "restecg",
    "exang",
    "slope",
    "ca",
    "thal",
]
SCORING = {
    "accuracy": "accuracy",
    "precision": "precision",
    "recall": "recall",
    "roc_auc": "roc_auc",
}
METRICS = tuple(SCORING)


def build_preprocessor() -> ColumnTransformer:
    """Build imputing, scaling, and encoding steps fit only on each training fold."""
    numeric_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def build_models() -> dict[str, BaseEstimator]:
    """Return the three preselected classifier candidates."""
    return {
        "logistic_regression": LogisticRegression(max_iter=2000),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            random_state=RANDOM_STATE,
            n_jobs=1,
        ),
        "rbf_svc": SVC(kernel="rbf"),
    }


def build_pipeline(estimator: BaseEstimator) -> Pipeline:
    """Combine fold-local preprocessing with a classifier."""
    return Pipeline(
        [
            ("preprocessor", build_preprocessor()),
            ("classifier", estimator),
        ]
    )


def select_champion(results: pd.DataFrame) -> str:
    """Rank candidates by recall, then ROC-AUC, then precision."""
    ranked = results.sort_values(
        ["recall_mean", "roc_auc_mean", "precision_mean"],
        ascending=False,
        kind="stable",
    )
    return str(ranked.iloc[0]["model"])


def evaluate_models(
    data: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, Pipeline]]:
    """Cross-validate each candidate and fit its full-data pipeline for later phases."""
    expected_features = NUMERIC_FEATURES + CATEGORICAL_FEATURES
    missing_columns = set(expected_features + [TARGET]).difference(data.columns)
    if missing_columns:
        raise ValueError(f"Processed dataset is missing columns: {sorted(missing_columns)}")
    if data.empty:
        raise ValueError("Processed dataset is empty")

    features = data[expected_features]
    target = data[TARGET]
    if target.isna().any() or not target.isin([0, 1]).all():
        raise ValueError("Target column 'num' must contain only non-missing values 0 and 1")

    cv = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)
    result_rows: list[dict[str, float | str]] = []
    fitted_pipelines: dict[str, Pipeline] = {}

    for name, estimator in build_models().items():
        pipeline = build_pipeline(estimator)
        scores = cross_validate(
            pipeline,
            features,
            target,
            cv=cv,
            scoring=SCORING,
            return_train_score=False,
            n_jobs=1,
            error_score="raise",
        )
        row: dict[str, float | str] = {"model": name}
        for metric in METRICS:
            values = scores[f"test_{metric}"]
            row[f"{metric}_mean"] = float(values.mean())
            row[f"{metric}_std"] = float(values.std(ddof=1))
        result_rows.append(row)

        pipeline.fit(features, target)
        fitted_pipelines[name] = pipeline

    results = pd.DataFrame(result_rows)
    return results, fitted_pipelines


def format_report(results: pd.DataFrame, champion: str) -> str:
    """Format cross-validation results and selection rationale as Markdown."""
    lines = [
        f"# Model comparison — Author: `{AUTHOR}`",
        "",
        f"- Validation: {N_SPLITS}-fold stratified cross-validation "
        f"(shuffle, `random_state={RANDOM_STATE}`).",
        "- Scores are mean ± sample standard deviation across folds.",
        "- Champion rule: highest mean recall, then ROC-AUC, then precision; "
        "accuracy is reported but is not the selection criterion.",
        f"- Selected champion: **{champion}**.",
        "",
        "| Model | Accuracy | Precision | Recall | ROC-AUC |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in results.itertuples(index=False):
        values = {
            metric: getattr(row, f"{metric}_mean")
            for metric in METRICS
        }
        deviations = {
            metric: getattr(row, f"{metric}_std")
            for metric in METRICS
        }
        lines.append(
            f"| {row.model} | "
            + " | ".join(
                f"{values[metric]:.4f} ± {deviations[metric]:.4f}"
                for metric in METRICS
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "Cross-validation scores estimate performance on held-out folds; "
            "they are not a claim of clinical readiness.",
        ]
    )
    return "\n".join(lines) + "\n"


def track_models(
    data: pd.DataFrame,
    data_path: Path,
    results: pd.DataFrame,
    pipelines: dict[str, Pipeline],
    champion: str,
    report_path: Path,
) -> None:
    """Persist candidate runs, artifacts, and the champion in the local registry."""
    os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
    os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "true"

    import mlflow
    import mlflow.sklearn
    from mlflow.models import infer_signature
    from mlflow.tracking import MlflowClient

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(f"%(levelname)s Author: {AUTHOR} %(message)s"))
    logger = logging.getLogger("mlflow")
    logger.handlers = [handler]
    logger.propagate = False

    figures = [
        ROOT / "reports" / "figures" / name
        for name in (
            "feature_histograms.png",
            "correlation_heatmap.png",
            "class_balance.png",
        )
    ]
    for figure in figures:
        if not figure.is_file():
            raise FileNotFoundError(f"Required EDA artifact not found: {figure}")

    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_registry_uri(TRACKING_URI)
    client = MlflowClient(tracking_uri=TRACKING_URI, registry_uri=TRACKING_URI)
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = client.create_experiment(
            EXPERIMENT_NAME,
            artifact_location=ARTIFACT_ROOT.as_uri(),
            tags={"author": AUTHOR},
        )
    else:
        if experiment.lifecycle_stage != "active":
            raise ValueError(f"MLflow experiment {EXPERIMENT_NAME!r} is not active")
        if experiment.artifact_location != ARTIFACT_ROOT.as_uri():
            raise ValueError("Existing MLflow experiment has an unexpected artifact location")
        experiment_id = experiment.experiment_id

    dataset_hash = hashlib.sha256(data_path.read_bytes()).hexdigest()
    features = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    input_example = features.head(3)
    records: list[dict[str, str]] = []
    for row in results.to_dict(orient="records"):
        name = str(row["model"])
        pipeline = pipelines[name]
        with mlflow.start_run(
            experiment_id=experiment_id,
            run_name=name,
            tags={
                "author": AUTHOR,
                "model": name,
                "champion": str(name == champion).lower(),
                "dataset_sha256": dataset_hash,
                "confidence_status": "uncalibrated",
            },
        ) as run:
            params = {
                key: str(value)
                for key, value in pipeline.get_params(deep=True).items()
            }
            params.update(
                {
                    "cv_folds": str(N_SPLITS),
                    "cv_seed": str(RANDOM_STATE),
                    "cv_shuffle": "true",
                    "rows": str(len(data)),
                    "features": json.dumps(list(features.columns)),
                    "selection_rule": "recall_mean, roc_auc_mean, precision_mean",
                }
            )
            mlflow.log_params(params)
            mlflow.log_metrics(
                {key: float(value) for key, value in row.items() if key != "model"}
            )
            for figure in figures:
                mlflow.log_artifact(str(figure), artifact_path="eda")
            mlflow.log_artifact(str(report_path), artifact_path="reports")
            model_info = mlflow.sklearn.log_model(
                sk_model=pipeline,
                name="pipeline",
                serialization_format="cloudpickle",
                signature=infer_signature(input_example, pipeline.predict(input_example)),
                input_example=input_example,
                pip_requirements=str(ROOT / "requirements.txt"),
                metadata={"author": AUTHOR, "confidence_status": "uncalibrated"},
            )
            records.append(
                {"model": name, "run_id": run.info.run_id, "model_uri": model_info.model_uri}
            )
        print(f"Logged {name}: run_id={run.info.run_id} (Author: {AUTHOR})")

    champion_record = next(record for record in records if record["model"] == champion)
    if not client.search_registered_models(f"name = '{REGISTERED_MODEL_NAME}'"):
        client.create_registered_model(REGISTERED_MODEL_NAME, tags={"author": AUTHOR})
    version = client.create_model_version(
        name=REGISTERED_MODEL_NAME,
        source=champion_record["model_uri"],
        run_id=champion_record["run_id"],
        tags={"author": AUTHOR, "confidence_status": "uncalibrated"},
    )
    lines = [
        f"# MLflow summary - Author: `{AUTHOR}`",
        "",
        f"- Tracking and registry URI: `{TRACKING_URI}`",
        f"- Experiment: `{EXPERIMENT_NAME}` (ID `{experiment_id}`).",
        f"- Artifact store: `{ARTIFACT_ROOT.as_uri()}`",
        f"- Dataset SHA-256: `{dataset_hash}`",
        "- Metrics are held-out CV means and sample standard deviations; "
        "logged pipelines are subsequently fit on all 303 rows.",
        "",
        "| Model | Run ID | Model URI |",
        "|---|---|---|",
        *[
            f"| {record['model']} | `{record['run_id']}` | `{record['model_uri']}` |"
            for record in records
        ],
        "",
        f"- Champion: `{champion}`; run ID: `{champion_record['run_id']}`.",
        f"- Registered model: `{REGISTERED_MODEL_NAME}`, version `{version.version}`.",
        f"- Registry URI: `models:/{REGISTERED_MODEL_NAME}/{version.version}`",
        "- Each run contains parameters, all four CV metrics and standard deviations, "
        "the complete fitted sklearn pipeline, three EDA figures, and the comparison report.",
        "- The champion is not calibrated and does not expose confidence probabilities. "
        "The confidence plan in docs/DECISIONS.md must be implemented and evaluated "
        "before packaging a confidence-bearing inference artifact in Phase 4.",
        "",
        "Reproduce: `python3 src/train/train.py` from the repository root. "
        "Each execution appends runs and a new registry version; the summary records "
        "the latest successful batch.",
    ]
    MLFLOW_SUMMARY_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"Registered {champion}: version={version.version}; "
        f"wrote {MLFLOW_SUMMARY_PATH} (Author: {AUTHOR})"
    )


def train(data_path: Path = DATA_PATH, report_path: Path = REPORT_PATH) -> pd.DataFrame:
    """Evaluate candidate models, print the comparison, and save its report."""
    data = pd.read_csv(data_path)
    results, pipelines = evaluate_models(data)
    champion = select_champion(results)
    report = format_report(results, champion)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    console_results = results.copy()
    console_results.insert(0, f"author={AUTHOR}", AUTHOR)
    print(f"Model comparison (Author: {AUTHOR})")
    print(console_results.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"Selected champion: {champion} (Author: {AUTHOR})")
    print(f"Wrote {report_path} (Author: {AUTHOR})")
    track_models(data, data_path, results, pipelines, champion, report_path)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="processed CSV path")
    parser.add_argument(
        "--report",
        type=Path,
        default=REPORT_PATH,
        help="Markdown comparison report path",
    )
    args = parser.parse_args()
    train(args.data, args.report)


if __name__ == "__main__":
    main()
