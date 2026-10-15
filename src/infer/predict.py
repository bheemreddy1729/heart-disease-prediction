"""Predict binary labels and class confidence using the trusted local pipeline."""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Mapping
from numbers import Real
from pathlib import Path
from typing import TypedDict

import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline

from src.train.train import AUTHOR, CATEGORICAL_FEATURES, NUMERIC_FEATURES, ROOT

MODEL_PATH = ROOT / "models" / "heart_pipeline.joblib"
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


class Prediction(TypedDict):
    prediction: int
    confidence: float


def predict_records(
    records: list[dict[str, float | int | None]],
) -> list[Prediction]:
    """Validate records and infer without fitting any preprocessing or estimator."""
    if not isinstance(records, list) or not records:
        raise ValueError("Expected a non-empty list of feature records")
    expected = set(FEATURES)
    for index, record in enumerate(records):
        if not isinstance(record, Mapping):
            raise ValueError(f"Record {index} must be a feature dictionary")
        if set(record) != expected:
            missing = sorted(expected.difference(record))
            extra = sorted(set(record).difference(expected), key=str)
            raise ValueError(f"Record {index}: missing keys {missing}, extra keys {extra}")
        for key, value in record.items():
            if value is not None and (
                isinstance(value, bool)
                or not isinstance(value, Real)
                or not math.isfinite(value)
            ):
                raise ValueError(f"Record {index} feature {key!r} must be finite numeric or null")

    if not MODEL_PATH.is_file():
        raise FileNotFoundError(
            f"Missing trusted model artifact {MODEL_PATH}; run python -m src.train.package"
        )
    pipeline = joblib.load(MODEL_PATH)
    if not isinstance(pipeline, Pipeline) or not hasattr(pipeline, "predict_proba"):
        raise ValueError("Artifact must be a complete probability-capable sklearn Pipeline")
    classes = np.asarray(pipeline.classes_)
    if classes.shape != (2,) or not np.array_equal(classes, [0, 1]):
        raise ValueError("Artifact must have classes [0, 1]")
    frame = pd.DataFrame.from_records(records, columns=FEATURES).astype(float)
    probabilities = pipeline.predict_proba(frame)
    if (
        probabilities.shape != (len(records), 2)
        or not np.isfinite(probabilities).all()
        or not ((probabilities >= 0) & (probabilities <= 1)).all()
        or not np.allclose(probabilities.sum(axis=1), 1)
    ):
        raise ValueError("Artifact returned invalid class probabilities")
    winners = probabilities.argmax(axis=1)
    return [
        {
            "prediction": int(classes[winner]),
            "confidence": float(probabilities[index, winner]),
        }
        for index, winner in enumerate(winners)
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="JSON list of feature records")
    args = parser.parse_args()
    try:
        records = json.loads(args.input.read_text(encoding="utf-8"))
        result = predict_records(records)
    except (OSError, ValueError) as error:
        print(f"Author: {AUTHOR} Inference failed: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(result, allow_nan=False))


if __name__ == "__main__":
    main()
