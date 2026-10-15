"""Compare heart-disease classifiers with leakage-safe stratified cross-validation."""

from __future__ import annotations

import argparse
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
                f"{values[metric]:.3f} ± {deviations[metric]:.3f}"
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


def train(data_path: Path = DATA_PATH, report_path: Path = REPORT_PATH) -> pd.DataFrame:
    """Evaluate candidate models, print the comparison, and save its report."""
    data = pd.read_csv(data_path)
    results, _ = evaluate_models(data)
    champion = select_champion(results)
    report = format_report(results, champion)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")

    print(f"Model comparison (Author: {AUTHOR})")
    print(results.to_string(index=False, float_format=lambda value: f"{value:.4f}"))
    print(f"Selected champion: {champion}")
    print(f"Wrote {report_path}")
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
