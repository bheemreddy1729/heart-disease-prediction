"""Evaluate and package the confidence-capable heart-disease pipeline."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import platform
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import Pipeline

from src.train.train import (
    AUTHOR,
    CATEGORICAL_FEATURES,
    DATA_PATH,
    N_SPLITS,
    NUMERIC_FEATURES,
    RANDOM_STATE,
    ROOT,
    TARGET,
    build_models,
    build_pipeline,
    evaluate_models,
    select_champion,
)

matplotlib.use("Agg")

import matplotlib.pyplot as plt

MODEL_PATH = ROOT / "models" / "heart_pipeline.joblib"
CALIBRATION_REPORT = ROOT / "reports" / "calibration_summary.md"
RELIABILITY_PATH = ROOT / "reports" / "figures" / "calibration_reliability.png"


def build_confidence_pipeline(champion: str) -> Pipeline:
    inner_cv = StratifiedKFold(
        n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE
    )
    return Pipeline(
        [
            (
                "calibrated_classifier",
                CalibratedClassifierCV(
                    estimator=build_pipeline(build_models()[champion]),
                    method="sigmoid",
                    cv=inner_cv,
                    ensemble=True,
                    n_jobs=1,
                ),
            )
        ]
    )


def package(data_path: Path = DATA_PATH) -> dict[str, float]:
    data = pd.read_csv(data_path)
    results, _ = evaluate_models(data)
    champion = select_champion(results)
    features = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    target = data[TARGET]
    outer_cv = StratifiedKFold(
        n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE
    )
    pipeline = build_confidence_pipeline(champion)
    probabilities = cross_val_predict(
        pipeline,
        features,
        target,
        cv=outer_cv,
        method="predict_proba",
        n_jobs=1,
    )
    predictions = np.argmax(probabilities, axis=1)
    positive_probabilities = probabilities[:, 1]
    baseline = np.empty(len(data), dtype=float)
    for train_indices, validation_indices in outer_cv.split(features, target):
        baseline[validation_indices] = target.iloc[train_indices].mean()

    metrics = {
        "accuracy": float(accuracy_score(target, predictions)),
        "precision": float(precision_score(target, predictions, zero_division=0)),
        "recall": float(recall_score(target, predictions)),
        "roc_auc": float(roc_auc_score(target, positive_probabilities)),
        "brier_score": float(brier_score_loss(target, positive_probabilities)),
        "log_loss": float(log_loss(target, probabilities)),
        "baseline_brier_score": float(brier_score_loss(target, baseline)),
    }
    fraction_positive, mean_predicted = calibration_curve(
        target, positive_probabilities, n_bins=5, strategy="uniform"
    )
    figure, (curve, histogram) = plt.subplots(1, 2, figsize=(11, 4))
    curve.plot([0, 1], [0, 1], "--", color="gray", label="Ideal calibration")
    curve.plot(mean_predicted, fraction_positive, "o-", label="Nested OOF sigmoid")
    curve.set(xlabel="Mean predicted P(disease)", ylabel="Observed disease fraction")
    curve.legend()
    histogram.hist(positive_probabilities, bins=np.linspace(0, 1, 6))
    histogram.set(xlabel="Predicted P(disease)", ylabel="Patients")
    figure.suptitle(f"Calibration diagnostics - Author: {AUTHOR}")
    figure.tight_layout()
    RELIABILITY_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(RELIABILITY_PATH, dpi=150)
    plt.close(figure)

    pipeline.fit(features, target)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, MODEL_PATH)
    provenance = {
        "author": AUTHOR,
        "candidate": champion,
        "rows": len(data),
        "features": list(features.columns),
        "dataset_sha256": hashlib.sha256(data_path.read_bytes()).hexdigest(),
        "artifact_sha256": hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),
        "python_version": platform.python_version(),
        "versions": {
            name: importlib.metadata.version(name)
            for name in ("scikit-learn", "numpy", "scipy", "pandas", "joblib")
        },
        "calibration": {
            "method": "sigmoid",
            "folds": N_SPLITS,
            "shuffle": True,
            "random_state": RANDOM_STATE,
            "ensemble": True,
        },
        "nested_oof_metrics": metrics,
    }
    MODEL_PATH.with_suffix(".json").write_text(
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
    report = [
        f"# Confidence pipeline diagnostics - Author: `{AUTHOR}`",
        "",
        f"- Selected candidate: `{champion}` using the established CV champion rule.",
        f"- Data: {len(data)} rows; SHA-256 `{provenance['dataset_sha256']}`.",
        "- Evaluation: 5 outer stratified folds, each with 5 inner sigmoid calibration "
        "folds; shuffled, seed 42. Preprocessing stays inside each inner estimator.",
        "- Scores below are pooled outer out-of-fold diagnostics, not the original "
        "uncalibrated model's fold-mean comparison.",
        "- Candidate selection used the same dataset; these post-selection diagnostics "
        "are not an unbiased independent test, clinical validation, or guarantee of calibration.",
        "",
        "| Metric | Value |",
        "|---|---:|",
        *[f"| {name} | {value:.6f} |" for name, value in metrics.items()],
        "",
        "Brier score and log loss are lower-is-better. The baseline uses only each "
        "outer training fold's disease prevalence; the reliability plot compares predicted "
        "probabilities to observed frequencies and shows bin counts. Small bins are uncertain.",
        "",
        "![Reliability diagram and probability counts](figures/calibration_reliability.png)",
        "",
        f"- Final artifact: `models/heart_pipeline.joblib`, fit on {len(data)} rows after OOF evaluation.",
        f"- Artifact SHA-256: `{provenance['artifact_sha256']}`.",
        "- Provenance: `models/heart_pipeline.json`; regenerate both with "
        "`python -m src.train.package`.",
        "- Inference returns the probability of the predicted class as confidence. "
        "It is not certainty, a diagnosis, or a decision threshold chosen for clinical use.",
        "- The existing MLflow registered version remains the uncalibrated Phase 3 model; "
        "this separate local confidence artifact does not change its recorded metrics.",
    ]
    CALIBRATION_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Author: {AUTHOR} Packaged {champion}: {MODEL_PATH}")
    print(f"Author: {AUTHOR} Nested OOF metrics: {json.dumps(metrics, sort_keys=True)}")
    print(f"Author: {AUTHOR} Wrote {CALIBRATION_REPORT}")
    return metrics


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH)
    args = parser.parse_args()
    package(args.data)
