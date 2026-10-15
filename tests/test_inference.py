import json
import sys
from unittest.mock import Mock

import joblib
import numpy as np
import pytest
from sklearn.pipeline import Pipeline
from sklearn.svm import SVC

from src.infer import predict


@pytest.fixture
def artifact(packaged, monkeypatch):
    path = packaged[0] / "heart_pipeline.joblib"
    monkeypatch.setattr(predict, "MODEL_PATH", path)
    return path


def test_real_serialized_inference_batch_and_nulls(artifact, records, monkeypatch):
    monkeypatch.setattr(Pipeline, "fit", Mock(side_effect=AssertionError("Inference must not fit")))
    first = predict.predict_records(records)
    assert first == predict.predict_records(records)
    assert first[0]["prediction"] == 0
    assert first[0]["confidence"] == pytest.approx(0.7466949562461239)
    assert set(first[0]) == {"prediction", "confidence"}
    assert type(first[0]["prediction"]) is int
    assert type(first[0]["confidence"]) is float
    assert 0.5 <= first[0]["confidence"] <= 1
    missing = dict(records[0], ca=None, thal=None)
    batch = predict.predict_records([records[0], missing])
    assert len(batch) == 2
    assert batch[0] == first[0]
    assert batch[1]["prediction"] in (0, 1)
    assert 0.5 <= batch[1]["confidence"] <= 1


@pytest.mark.parametrize("positive, label", [(0.49, 0), (0.5, 0), (0.51, 1)])
def test_probability_threshold_and_exact_tie(artifact, records, monkeypatch, positive, label):
    monkeypatch.setattr(
        Pipeline, "predict_proba", lambda self, frame: np.array([[1 - positive, positive]])
    )
    assert predict.predict_records(records) == [
        {"prediction": label, "confidence": max(positive, 1 - positive)}
    ]


@pytest.mark.parametrize("records", [[], {}, None, [42]])
def test_invalid_containers(records):
    with pytest.raises(ValueError, match="non-empty list|feature dictionary"):
        predict.predict_records(records)


@pytest.mark.parametrize("value", [True, "63", float("nan"), float("inf"), -float("inf")])
def test_invalid_feature_values(records, value):
    records[0]["age"] = value
    with pytest.raises(ValueError, match="finite numeric or null"):
        predict.predict_records(records)


@pytest.mark.parametrize("kind", ["missing", "extra"])
def test_exact_feature_keys(records, kind):
    if kind == "missing":
        records[0].pop("age")
    else:
        records[0]["num"] = 0
    with pytest.raises(ValueError, match="missing keys.*extra keys"):
        predict.predict_records(records)


def test_missing_artifact(tmp_path, records, monkeypatch):
    monkeypatch.setattr(predict, "MODEL_PATH", tmp_path / "absent.joblib")
    with pytest.raises(FileNotFoundError, match="Missing trusted model artifact"):
        predict.predict_records(records)


@pytest.mark.parametrize("model", [{"not": "pipeline"}, Pipeline([("classifier", SVC())])])
def test_wrong_artifact(tmp_path, records, monkeypatch, model):
    path = tmp_path / "invalid.joblib"
    joblib.dump(model, path)
    monkeypatch.setattr(predict, "MODEL_PATH", path)
    with pytest.raises(ValueError, match="probability-capable sklearn Pipeline"):
        predict.predict_records(records)


@pytest.mark.parametrize(
    "probabilities",
    [
        [[0.2, 0.2]], [[-0.1, 1.1]], [[np.nan, 0.5]], [[np.inf, 0.5]],
        [[1.0]], [[0.5, 0.5], [0.5, 0.5]],
    ],
)
def test_invalid_model_probabilities(artifact, records, monkeypatch, probabilities):
    monkeypatch.setattr(
        Pipeline, "predict_proba", lambda self, frame: np.array(probabilities)
    )
    with pytest.raises(ValueError, match="invalid class probabilities"):
        predict.predict_records(records)


def test_reversed_classes_rejected(artifact, records, monkeypatch):
    pipeline = joblib.load(artifact)
    pipeline.named_steps["calibrated_classifier"].classes_ = np.array([1, 0])
    monkeypatch.setattr(predict.joblib, "load", lambda path: pipeline)
    with pytest.raises(ValueError, match=r"classes \[0, 1\]"):
        predict.predict_records(records)


def test_cli_json_only(artifact, records, tmp_path, monkeypatch, capsys):
    source = tmp_path / "patient.json"
    source.write_text(json.dumps(records))
    monkeypatch.setattr(sys, "argv", ["predict", "--input", str(source)])
    predict.main()
    captured = capsys.readouterr()
    assert not captured.err
    assert json.loads(captured.out) == predict.predict_records(records)


@pytest.mark.parametrize("content", ["not-json", "[]", '[{"age": true}]'])
def test_cli_errors_are_attributed_and_nonzero(tmp_path, monkeypatch, capsys, content):
    source = tmp_path / "invalid.json"
    source.write_text(content)
    monkeypatch.setattr(sys, "argv", ["predict", "--input", str(source)])
    with pytest.raises(SystemExit) as error:
        predict.main()
    assert error.value.code == 1
    captured = capsys.readouterr()
    assert not captured.out
    assert "Author: 2025ae05142 Inference failed:" in captured.err
