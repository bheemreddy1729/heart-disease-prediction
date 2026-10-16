"""HTTP interface for the trusted, locally packaged heart-disease pipeline."""

from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.infer.predict import predict_records

app = FastAPI(
    title="Heart disease prediction",
    description="Author: 2025ae05142. Coursework inference; not a medical diagnostic tool.",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Report that the API process is responsive."""
    return {"status": "ok"}


class PredictionResponse(BaseModel):
    prediction: int = Field(ge=0, le=1)
    confidence: float = Field(ge=0.5, le=1)


@app.post("/predict", response_model=list[PredictionResponse])
def predict(payload: Any = Body(...)) -> list[dict[str, int | float]]:
    """Return predictions for a non-empty list of feature records."""
    try:
        return predict_records(payload)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
