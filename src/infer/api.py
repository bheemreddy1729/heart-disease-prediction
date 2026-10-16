"""HTTP interface for the trusted, locally packaged heart-disease pipeline."""

from __future__ import annotations

import json
import logging
import sys
import time
from datetime import UTC, datetime
from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.responses import Response

from src.infer.predict import predict_records

METRICS_REGISTRY = CollectorRegistry()
PREDICTION_REQUESTS = Counter(
    "heart_disease_prediction_requests",
    "Number of prediction requests received",
    registry=METRICS_REGISTRY,
)
PREDICTION_LATENCY = Histogram(
    "heart_disease_prediction_request_duration_seconds",
    "Time spent processing prediction requests",
    registry=METRICS_REGISTRY,
)

logger = logging.getLogger("heart_disease.api")
logger.setLevel(logging.INFO)
logger.propagate = False
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)

app = FastAPI(
    title="Heart disease prediction",
    description="Author: 2025ae05142. Coursework inference; not a medical diagnostic tool.",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process is responsive."""
    return {"status": "ok"}


@app.get("/metrics", include_in_schema=False)
def metrics() -> Response:
    """Expose Prometheus request and latency metrics."""
    return Response(generate_latest(METRICS_REGISTRY), media_type=CONTENT_TYPE_LATEST)


class PredictionResponse(BaseModel):
    prediction: int = Field(ge=0, le=1)
    confidence: float = Field(ge=0.5, le=1)


@app.post("/predict", response_model=list[PredictionResponse])
def predict(payload: Any = Body(...)) -> list[dict[str, int | float]]:
    """Return predictions and emit privacy-conscious request telemetry."""
    started = time.perf_counter()
    prediction: int | list[int] | None = None
    confidence: float | list[float] | None = None
    feature_keys = (
        sorted(
            {
                key
                for record in payload
                if isinstance(record, dict)
                for key in record
                if isinstance(key, str)
            }
        )
        if isinstance(payload, list)
        else []
    )
    try:
        result = predict_records(payload)
        predictions = [item["prediction"] for item in result]
        confidences = [item["confidence"] for item in result]
        prediction = predictions[0] if len(predictions) == 1 else predictions
        confidence = confidences[0] if len(confidences) == 1 else confidences
        return result
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    finally:
        duration = time.perf_counter() - started
        PREDICTION_REQUESTS.inc()
        PREDICTION_LATENCY.observe(duration)
        logger.info(
            json.dumps(
                {
                    "author": "2025ae05142",
                    "timestamp": datetime.now(UTC).isoformat(),
                    "feature_keys": feature_keys,
                    "prediction": prediction,
                    "confidence": confidence,
                    "latency_ms": round(duration * 1000, 3),
                },
                separators=(",", ":"),
                allow_nan=False,
            )
        )
