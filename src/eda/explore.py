"""Create exploratory figures and a summary for the processed UCI dataset."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "heart.csv"
FIGURES_PATH = ROOT / "reports" / "figures"
SUMMARY_PATH = ROOT / "reports" / "eda_summary.md"
AUTHOR = "2025ae05142"
TARGET = "num"


def write_histograms(data: pd.DataFrame, path: Path) -> None:
    features = [column for column in data.columns if column != TARGET]
    rows = (len(features) + 3) // 4
    figure, axes = plt.subplots(rows, 4, figsize=(16, 3.5 * rows), squeeze=False)
    for axis, column in zip(axes.flat, features):
        values = data[column].dropna()
        axis.hist(values, bins=min(max(values.nunique(), 5), 20), color="#3973ac")
        axis.set_title(column)
        axis.set_xlabel(column)
        axis.set_ylabel("Count")
    for axis in axes.flat[len(features) :]:
        axis.set_visible(False)
    figure.suptitle("Numeric clinical feature histograms")
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def write_correlation_heatmap(data: pd.DataFrame, path: Path) -> None:
    features = [column for column in data.columns if column != TARGET]
    correlation = data[features].corr()
    figure, axis = plt.subplots(figsize=(12, 10))
    image = axis.imshow(correlation, cmap="coolwarm", vmin=-1, vmax=1)
    axis.set_xticks(range(len(features)), labels=features, rotation=45, ha="right")
    axis.set_yticks(range(len(features)), labels=features)
    axis.set_title("Clinical feature correlation (pairwise complete observations)")
    figure.colorbar(image, ax=axis, label="Pearson correlation")
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def write_class_balance(data: pd.DataFrame, path: Path) -> None:
    counts = data[TARGET].value_counts().reindex([0, 1], fill_value=0)
    figure, axis = plt.subplots(figsize=(6, 4))
    bars = axis.bar(["Absent (0)", "Present (1)"], counts.values, color=["#3973ac", "#d97941"])
    axis.bar_label(bars)
    axis.set_title("Heart disease class balance")
    axis.set_ylabel("Patients")
    figure.tight_layout()
    figure.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(figure)


def write_summary(data: pd.DataFrame, path: Path) -> None:
    missing = data.isna().sum()
    counts = data[TARGET].value_counts().reindex([0, 1], fill_value=0)
    lines = [
        f"# EDA summary — Author: `{AUTHOR}`",
        "",
        f"- Rows: {len(data)}",
        f"- Features: {len(data.columns) - 1}",
        f"- Missing cells: {int(missing.sum())}",
        "",
        "## Missing values by column",
        "",
        "| Column | Missing | Percent of rows |",
        "|---|---:|---:|",
    ]
    lines.extend(
        f"| {column} | {int(value)} | {value / len(data) * 100:.2f}% |"
        for column, value in missing.items()
    )
    lines.extend(
        [
            "",
            "## Binarized target counts",
            "",
            "| Class | Count |",
            "|---|---:|",
            f"| Absent (0) | {int(counts.loc[0])} |",
            f"| Present (1) | {int(counts.loc[1])} |",
            "",
            "Feature histograms and correlations omit missing feature values; "
            "the processed table retains them.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def explore(data_path: Path = DATA_PATH) -> None:
    data = pd.read_csv(data_path)
    if TARGET not in data:
        raise ValueError(f"Processed dataset must contain target column {TARGET!r}")
    if data.empty:
        raise ValueError(f"Processed dataset is empty: {data_path}")
    if not data[TARGET].isin([0, 1]).all():
        raise ValueError("Processed target column 'num' must be binary (0 or 1)")

    FIGURES_PATH.mkdir(parents=True, exist_ok=True)
    write_histograms(data, FIGURES_PATH / "feature_histograms.png")
    write_correlation_heatmap(data, FIGURES_PATH / "correlation_heatmap.png")
    write_class_balance(data, FIGURES_PATH / "class_balance.png")
    write_summary(data, SUMMARY_PATH)
    print(f"Wrote EDA figures to {FIGURES_PATH} and summary to {SUMMARY_PATH}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA_PATH, help="processed CSV path")
    args = parser.parse_args()
    explore(args.data)
