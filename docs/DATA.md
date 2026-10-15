# Data source

Author: `2025ae05142`

- Dataset: UCI Heart Disease, dataset 45, processed Cleveland subset.
- Source URL: <https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data>
- Download date: 2026-10-15.
- Reproduce with `python src/data/download_heart.py`, then clean with `python src/data/prepare.py`.
- The downloaded source is written to `data/raw/processed.cleveland.data`; `data/raw/README.md` points to the source and records the local download date. The processed table is `data/processed/heart.csv`.
- The dataset contains 303 patient records and 14 source columns: 13 clinical features and the original `num` target. The target is mapped to 0 for absence and 1 for presence (original values 1–4).

Values represented by `?` in the source are parsed as missing. The processed CSV keeps these values blank instead of estimating or discarding them; the EDA summary reports their counts. EDA histograms omit missing values per feature and correlations use pairwise complete observations. No imputation statistics are calculated during this phase.
