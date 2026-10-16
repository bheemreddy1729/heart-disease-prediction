import json

from fastapi.testclient import TestClient
from prometheus_client.parser import text_string_to_metric_families

from src.infer import api

client = TestClient(api.app)


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict_returns_contract_shape(records, monkeypatch):
    expected = [{"prediction": 0, "confidence": 0.75}]
    monkeypatch.setattr(api, "predict_records", lambda payload: expected)

    response = client.post("/predict", json=records)

    assert response.status_code == 200
    assert response.json() == expected


def test_predict_rejects_invalid_records(records):
    records[0]["age"] = True

    response = client.post("/predict", json=records)

    assert response.status_code == 422
    assert "finite numeric or null" in response.json()["detail"]


def test_predict_rejects_empty_batch():
    response = client.post("/predict", json=[])

    assert response.status_code == 422
    assert "non-empty list" in response.json()["detail"]


def test_predict_emits_privacy_conscious_json_log(records, monkeypatch):
    log_lines = []
    monkeypatch.setattr(api.logger, "info", log_lines.append)

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


def test_invalid_prediction_is_logged_counted_and_exposed_in_metrics(records, monkeypatch):
    log_lines = []
    monkeypatch.setattr(api.logger, "info", log_lines.append)
    before = client.get("/metrics")
    before_count = next(
        sample.value
        for family in text_string_to_metric_families(before.text)
        for sample in family.samples
        if sample.name == "heart_disease_prediction_requests_total"
    )
    records[0]["age"] = True

    response = client.post("/predict", json=records)
    metrics_response = client.get("/metrics")

    after_count = next(
        sample.value
        for family in text_string_to_metric_families(metrics_response.text)
        for sample in family.samples
        if sample.name == "heart_disease_prediction_requests_total"
    )
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
