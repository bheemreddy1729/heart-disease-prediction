"""Validate and clean the UCI processed Cleveland heart-disease dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_PATH = ROOT / "data" / "raw" / "processed.cleveland.data"
PROCESSED_PATH = ROOT / "data" / "processed" / "heart.csv"
AUTHOR = "2025ae05142"

COLUMNS = [
    "age",
    "sex",
    "cp",
    "trestbps",
    "chol",
    "fbs",
    "restecg",
    "thalach",
    "exang",
    "oldpeak",
    "slope",
    "ca",
    "thal",
    "num",
]


def load_raw_data(path: Path = RAW_PATH) -> pd.DataFrame:
    """Read the headerless UCI file and validate its numeric fields and target."""
    data = pd.read_csv(
        path,
        header=None,
        names=COLUMNS,
        na_values=["?"],
        skipinitialspace=True,
    )
    if data.empty:
        raise ValueError(f"Dataset is empty: {path}")

    for column in COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="raise")

    if data["num"].isna().any():
        raise ValueError("Target column 'num' must not contain missing values")
    if not data["num"].isin([0, 1, 2, 3, 4]).all():
        raise ValueError("Target column 'num' must contain only values 0 through 4")

    return data


def prepare_dataframe(data: pd.DataFrame) -> pd.DataFrame:
    """Return numeric features and the binary target without imputing missing values."""
    cleaned = data.copy()
    cleaned["num"] = (cleaned["num"] > 0).astype("int64")
    return cleaned


def prepare_file(input_path: Path = RAW_PATH, output_path: Path = PROCESSED_PATH) -> Path:
    """Clean the downloaded dataset and write the processed CSV."""
    cleaned = prepare_dataframe(load_raw_data(input_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=RAW_PATH, help="path to the raw UCI file")
    parser.add_argument(
        "--output",
        type=Path,
        default=PROCESSED_PATH,
        help="path for the cleaned CSV",
    )
    args = parser.parse_args()
    output_path = prepare_file(args.input, args.output)
    print(f"Wrote {output_path} (Author: {AUTHOR})")


if __name__ == "__main__":
    main()
