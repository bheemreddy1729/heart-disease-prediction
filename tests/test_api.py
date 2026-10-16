import json

import pytest
from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from src.infer import api
from src.infer import predict as inference

client = TestClient(api.app)


def prediction_request_count():
    response = client.get("/metrics")
    return next(
        sample.value
        for family in text_string_to_metric_families(response.text)
        for sample in family.samples
        if sample.name == "heart_disease_prediction_requests_total"
    )


def prediction_duration_count():
    response = client.get("/metrics")
    return next(
        sample.value
        for family in text_string_to_metric_families(response.text)
        for sample in family.samples
        if sample.name == "heart_disease_prediction_request_duration_seconds_count"
    )


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_returns_contract_shape(records, monkeypatch):
    expected = [{"prediction": 0, "confidence": 0.75}]
    monkeypatch.setattr(api, "predict_records", lambda payload: expected)
    before_count = prediction_request_count()
    before_duration_count = prediction_duration_count()

    response = client.post("/predict", json=records)

    assert response.status_code == 200
    assert response.json() == expected
    assert prediction_request_count() == before_count + 1
    assert prediction_duration_count() == before_duration_count + 1


def test_predict_rejects_invalid_records(records):
    records[0]["age"] = True

    response = client.post("/predict", json=records)

    assert response.status_code == 422
    assert "finite numeric or null" in response.json()["detail"]


def test_predict_rejects_empty_batch():
    response = client.post("/predict", json=[])

    assert response.status_code == 422
    assert "non-empty list" in response.json()["detail"]


def test_predict_emits_privacy_conscious_json_log(records, packaged, monkeypatch):
    directory, _ = packaged
    log_lines = []
    monkeypatch.setattr(api.logger, "info", log_lines.append)
    monkeypatch.setattr(inference, "MODEL_PATH", directory / "heart_pipeline.joblib")

    response = client.post("/predict", json=records)

    assert response.status_code == 200
    assert len(log_lines) == 1
    event = json.loads(log_lines[0])
    assert event["author"] == "2025ae05142"
    assert event["feature_keys"] == sorted(records[0])
    assert event["prediction"] == response.json()[0]["prediction"]
    assert event["confidence"] == response.json()[0]["confidence"]
    assert isinstance(event["timestamp"], str)
    assert isinstance(event["latency_ms"], float)
    assert set(event) == {
        "author",
        "timestamp",
        "feature_keys",
        "prediction",
        "confidence",
        "latency_ms",
    }


@pytest.mark.parametrize(
    ("body", "headers"),
    [
        (b'{"age":', {"Content-Type": "application/json"}),
        (None, {}),
    ],
    ids=("malformed-json", "missing-body"),
)
def test_invalid_json_and_missing_body_are_logged_and_counted(body, headers, monkeypatch):
    log_lines = []
    monkeypatch.setattr(api.logger, "info", log_lines.append)
    before_count = prediction_request_count()
    before_duration_count = prediction_duration_count()

    response = client.post("/predict", content=body, headers=headers)

    assert response.status_code == 422
    assert prediction_request_count() == before_count + 1
    assert prediction_duration_count() == before_duration_count + 1
    assert len(log_lines) == 1
    event = json.loads(log_lines[0])
    assert event["author"] == "2025ae05142"
    assert event["feature_keys"] == []
    assert event["prediction"] is None
    assert event["confidence"] is None


def test_invalid_prediction_is_logged_counted_and_exposed_in_metrics(records, monkeypatch):
    log_lines = []
    monkeypatch.setattr(api.logger, "info", log_lines.append)
    before_count = prediction_request_count()
    records[0]["age"] = True

    response = client.post("/predict", json=records)
    metrics_response = client.get("/metrics")

    after_count = prediction_request_count()
    assert response.status_code == 422
    assert after_count == before_count + 1
    assert len(log_lines) == 1
    event = json.loads(log_lines[0])
    assert event["prediction"] is None
    assert event["confidence"] is None
    assert "age" in event["feature_keys"]
    assert metrics_response.status_code == 200
    assert any(
        sample.name == "heart_disease_prediction_request_duration_seconds_count"
        for family in text_string_to_metric_families(metrics_response.text)
        for sample in family.samples
    )
