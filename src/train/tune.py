"""Run a bounded, non-promoting RBF SVC tuning experiment."""

from __future__ import annotations

import hashlib
import json
import logging
import os

os.environ["MLFLOW_DISABLE_TELEMETRY"] = "true"
os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "true"

import tempfile
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.svm import SVC

from src.train.train import (
    ARTIFACT_ROOT,
    AUTHOR,
    DATA_PATH,
    METRICS,
    N_SPLITS,
    RANDOM_STATE,
    ROOT,
    TRACKING_URI,
    build_preprocessor,
    evaluate_candidates,
    select_champion,
)

EXPERIMENT_NAME = "heart-disease-tuning-2025ae05142"
REPORT_PATH = ROOT / "reports" / "tuning_summary.md"
C_VALUES = (0.1, 1.0, 10.0)
GAMMA_VALUES = ("scale", 0.01, 0.1)
BASELINE = "C=1,gamma=scale"


def build_candidates() -> dict[str, SVC]:
    """Return the predeclared grid in deterministic tie-breaking order."""
    return {
        f"C={c:g},gamma={gamma}": SVC(C=c, gamma=gamma, kernel="rbf")
        for c in C_VALUES
        for gamma in GAMMA_VALUES
    }


def format_report(
    results: pd.DataFrame, selected: str, run_ids: dict[str, str], dataset_hash: str
) -> str:
    baseline = results.set_index("model").loc[BASELINE]
    winner = results.set_index("model").loc[selected]
    lines = [
        f"# RBF SVC tuning summary - Author: `{AUTHOR}`",
        "",
        f"- Experiment: `{EXPERIMENT_NAME}`; tracking URI: `{TRACKING_URI}`.",
        f"- Dataset SHA-256: `{dataset_hash}`.",
        f"- Validation: {N_SPLITS} shuffled stratified folds, seed {RANDOM_STATE}.",
        "- Reuses fold-local imputation, scaling, and encoding from baseline training.",
        "- Ranking: mean recall, then ROC-AUC, then precision; exact ties retain grid order.",
        f"- Baseline: `{BASELINE}`; selected tuning configuration: `{selected}`.",
        "- Scores are fold means +/- sample standard deviations, not independent test scores.",
        "",
        "| Configuration | Accuracy | Precision | Recall | ROC-AUC | MLflow run ID |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in results.to_dict(orient="records"):
        name = str(row["model"])
        scores = " | ".join(
            f"{row[f'{metric}_mean']:.6f} +/- {row[f'{metric}_std']:.6f}"
            for metric in METRICS
        )
        lines.append(f"| {name} | {scores} | `{run_ids[name]}` |")
    lines.extend(
        [
            "",
            "## Selected configuration minus original baseline (CV mean differences)",
            "",
            *[
                f"- {metric}: {winner[f'{metric}_mean'] - baseline[f'{metric}_mean']:+.6f}"
                for metric in METRICS
            ],
            "",
            "The same dataset was used for original candidate selection and tuning. "
            "These differences are selection results, not proof of generalization improvement "
            "or clinical validation. The grid does not establish a global optimum.",
            "",
            "Each run records parameters, metrics, configuration scores, a comparison plot, and this "
            "summary. No registered model or serving artifact is changed. The deployed "
            "calibrated baseline remains unchanged pending an explicit promotion decision.",
            "",
            "Reproduce on the VM: `.venv/bin/python -m src.train.tune`. "
            "This appends tuning runs and updates only this tuning summary.",
        ]
    )
    return "\n".join(lines) + "\n"


def tune() -> pd.DataFrame:
    """Evaluate and log the grid without modifying baseline or serving artifacts."""
    import mlflow
    from mlflow.tracking import MlflowClient

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(f"%(levelname)s Author: {AUTHOR} %(message)s"))
    logger = logging.getLogger("mlflow")
    logger.handlers = [handler]
    logger.propagate = False

    data_bytes = DATA_PATH.read_bytes()
    dataset_hash = hashlib.sha256(data_bytes).hexdigest()
    data = pd.read_csv(DATA_PATH)
    candidates = build_candidates()
    if BASELINE not in candidates:
        raise ValueError("The tuning grid must include the original baseline")
    results, _ = evaluate_candidates(data, candidates)
    selected = select_champion(results)
    mlflow.set_tracking_uri(TRACKING_URI)
    client = MlflowClient(tracking_uri=TRACKING_URI)
    artifact_uri = (ARTIFACT_ROOT / "tuning").as_uri()
    experiment = client.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        experiment_id = client.create_experiment(
            EXPERIMENT_NAME, artifact_location=artifact_uri, tags={"author": AUTHOR}
        )
    else:
        if experiment.lifecycle_stage != "active" or experiment.artifact_location != artifact_uri:
            raise ValueError("Existing tuning experiment has unexpected lifecycle or artifact location")
        experiment_id = experiment.experiment_id

    run_ids: dict[str, str] = {}
    with tempfile.TemporaryDirectory(prefix="heart-tuning-") as directory:
        plot_path = Path(directory) / "tuning_comparison.png"
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.errorbar(
            range(len(results)), results["recall_mean"], yerr=results["recall_std"], fmt="o"
        )
        ax.set_xticks(range(len(results)), results["model"], rotation=45, ha="right")
        ax.set_ylabel("CV recall mean +/- sample standard deviation")
        ax.set_title(f"RBF SVC tuning - Author: {AUTHOR}")
        fig.tight_layout()
        fig.savefig(plot_path)
        plt.close(fig)
        for row in results.to_dict(orient="records"):
            name = str(row["model"])
            with mlflow.start_run(
                experiment_id=experiment_id,
                run_name=name,
                tags={
                    "author": AUTHOR,
                    "model": "rbf_svc",
                    "dataset_sha256": dataset_hash,
                    "selected": str(name == selected).lower(),
                    "baseline": str(name == BASELINE).lower(),
                    "evaluation_status": "tuning_selection_not_independent_test",
                    "promotion_status": "not_promoted",
                },
            ) as run:
                params = {
                    key: str(value)
                    for key, value in candidates[name].get_params().items()
                }
                params.update(
                    cv_folds=str(N_SPLITS),
                    cv_seed=str(RANDOM_STATE),
                    cv_shuffle="true",
                    rows=str(len(data)),
                    selection_rule="recall_mean, roc_auc_mean, precision_mean",
                    preprocessing="src.train.train.build_preprocessor",
                    search_grid=json.dumps(
                        {key: estimator.get_params() for key, estimator in candidates.items()}
                    ),
                )
                mlflow.log_params(params)
                mlflow.log_metrics(
                    {key: float(value) for key, value in row.items() if key != "model"}
                )
                mlflow.log_dict(row, "configuration_scores.json")
                mlflow.log_dict(
                    {
                        "author": AUTHOR,
                        "preprocessing": {
                            key: str(value)
                            for key, value in build_preprocessor().get_params(deep=True).items()
                        },
                        "dependencies": (ROOT / "requirements.txt").read_text(encoding="utf-8"),
                    },
                    "reproducibility.json",
                )
                mlflow.log_artifact(str(plot_path), artifact_path="plots")
                run_ids[name] = run.info.run_id
            print(f"Author: {AUTHOR} logged tuning configuration {name}: {run_ids[name]}")
        report = format_report(results, selected, run_ids, dataset_hash)
        staged_report = Path(directory) / REPORT_PATH.name
        staged_report.write_text(report, encoding="utf-8")
        for run_id in run_ids.values():
            client.log_artifact(run_id, str(staged_report), artifact_path="reports")
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Author: {AUTHOR} selected {selected}; wrote {REPORT_PATH}; no promotion")
    return results


if __name__ == "__main__":
    tune()
