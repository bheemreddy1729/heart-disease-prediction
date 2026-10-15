import hashlib
import json

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from src.train.train import AUTHOR, CATEGORICAL_FEATURES, NUMERIC_FEATURES


def test_real_packaging_provenance_and_complete_calibration(packaged, data):
    directory, metrics = packaged
    artifact = directory / "heart_pipeline.joblib"
    provenance = json.loads(artifact.with_suffix(".json").read_text())
    assert provenance["author"] == AUTHOR
    assert provenance["candidate"] == "rbf_svc"
    assert provenance["rows"] == len(data)
    assert provenance["features"] == NUMERIC_FEATURES + CATEGORICAL_FEATURES
    assert provenance["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert provenance["dataset_sha256"] == hashlib.sha256(
        (directory / "heart.csv").read_bytes()
    ).hexdigest()
    assert provenance["nested_oof_metrics"] == metrics
    assert all(np.isfinite(value) for value in metrics.values())
    assert metrics["brier_score"] < metrics["baseline_brier_score"]
    assert metrics["log_loss"] > 0
    for name in ("accuracy", "precision", "recall", "roc_auc", "brier_score"):
        assert 0 <= metrics[name] <= 1
    pipeline = joblib.load(artifact)
    assert isinstance(pipeline, Pipeline)
    calibrator = pipeline.named_steps["calibrated_classifier"]
    assert calibrator.method == "sigmoid"
    assert calibrator.ensemble is True
    assert calibrator.cv.n_splits == 5
    assert calibrator.cv.shuffle and calibrator.cv.random_state == 42
    assert len(calibrator.calibrated_classifiers_) == 5
    for fitted in calibrator.calibrated_classifiers_:
        assert isinstance(fitted.estimator, Pipeline)
        assert "preprocessor" in fitted.estimator.named_steps
        assert hasattr(fitted.estimator.named_steps["preprocessor"], "transformers_")
    report = (directory / "calibration_summary.md").read_text()
    assert AUTHOR in report
    assert "not an unbiased independent test" in report
    assert "exact tie at 0.5 returns class 0" in report
    assert (directory / "calibration_reliability.png").read_bytes().startswith(b"\x89PNG")
