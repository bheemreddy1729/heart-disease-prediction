import hashlib

import numpy as np
import pytest

from src.train import tune as tuning
from src.train.train import AUTHOR, METRICS, evaluate_candidates, select_champion


def test_grid_has_nine_unique_configurations_and_original_baseline():
    candidates = tuning.build_candidates()
    assert len(candidates) == 9
    assert list(candidates) == [
        f"C={c:g},gamma={gamma}"
        for c in (0.1, 1.0, 10.0)
        for gamma in ("scale", 0.01, 0.1)
    ]
    assert candidates[tuning.BASELINE].get_params()["C"] == 1
    assert candidates[tuning.BASELINE].get_params()["gamma"] == "scale"
    assert all(model.kernel == "rbf" for model in candidates.values())


def test_empty_candidates_fail_explicitly(data):
    with pytest.raises(ValueError, match="At least one candidate"):
        evaluate_candidates(data, {})


def test_reduced_real_tuning_is_isolated_and_logs_evidence(data, tmp_path, monkeypatch):
    from mlflow.tracking import MlflowClient

    source = tmp_path / "heart.csv"
    data.to_csv(source, index=False)
    report = tmp_path / "reports" / "tuning_summary.md"
    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    artifacts = tmp_path / "mlruns"
    monkeypatch.setattr(tuning, "DATA_PATH", source)
    monkeypatch.setattr(tuning, "REPORT_PATH", report)
    monkeypatch.setattr(tuning, "TRACKING_URI", uri)
    monkeypatch.setattr(tuning, "ARTIFACT_ROOT", artifacts)
    monkeypatch.setattr(tuning, "C_VALUES", (1.0,))
    monkeypatch.setattr(tuning, "GAMMA_VALUES", ("scale", 0.1))

    results = tuning.tune()
    assert len(results) == 2
    assert np.isfinite(results.drop(columns="model").to_numpy()).all()
    for metric in METRICS:
        assert results[f"{metric}_mean"].between(0, 1).all()
        assert (results[f"{metric}_std"] >= 0).all()
    baseline = results.set_index("model").loc[tuning.BASELINE]
    assert baseline["recall_mean"] == pytest.approx(0.8055555555555556)
    text = report.read_text()
    assert AUTHOR in text
    assert select_champion(results) in text
    assert "not independent test scores" in text
    assert "pending an explicit promotion decision" in text
    client = MlflowClient(tracking_uri=uri)
    experiment = client.get_experiment_by_name(tuning.EXPERIMENT_NAME)
    runs = client.search_runs([experiment.experiment_id])
    assert len(runs) == 2
    assert not client.search_registered_models()
    for run in runs:
        assert run.info.status == "FINISHED"
        assert run.info.run_id in text
        assert run.data.tags["author"] == AUTHOR
        assert run.data.tags["promotion_status"] == "not_promoted"
        assert run.data.tags["dataset_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
        assert set(run.data.metrics) == {
            f"{metric}_{stat}" for metric in METRICS for stat in ("mean", "std")
        }
        assert run.data.params["cv_folds"] == "5"
        assert run.data.params["C"] == "1.0"
        assert run.data.params["preprocessing"] == "src.train.train.build_preprocessor"
        assert {item.path for item in client.list_artifacts(run.info.run_id)} == {
            "configuration_scores.json", "reproducibility.json", "plots", "reports"
        }
        assert client.list_artifacts(run.info.run_id, "plots")[0].file_size > 0
        assert client.list_artifacts(run.info.run_id, "reports")[0].file_size > 0
    assert not (tmp_path / "models").exists()
    assert not (report.parent / "model_comparison.md").exists()


def test_missing_baseline_rejected_before_tracking(data, tmp_path, monkeypatch):
    source = tmp_path / "heart.csv"
    data.to_csv(source, index=False)
    monkeypatch.setattr(tuning, "DATA_PATH", source)
    monkeypatch.setattr(tuning, "C_VALUES", (0.1,))
    with pytest.raises(ValueError, match="must include the original baseline"):
        tuning.tune()
