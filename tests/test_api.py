from fastapi.testclient import TestClient

from src.infer import api

client = TestClient(api.app)


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
