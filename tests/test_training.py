import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, cross_validate

from src.train.train import (
    AUTHOR,
    CATEGORICAL_FEATURES,
    METRICS,
    NUMERIC_FEATURES,
    SCORING,
    build_models,
    build_pipeline,
    evaluate_models,
    format_report,
    select_champion,
)


def test_real_candidate_evaluation_and_fitted_pipelines(data, evaluated):
    results, pipelines = evaluated
    assert list(results["model"]) == list(build_models())
    assert set(results.columns) == {"model"} | {
        f"{metric}_{stat}" for metric in METRICS for stat in ("mean", "std")
    }
    assert np.isfinite(results.drop(columns="model").to_numpy()).all()
    for metric in METRICS:
        assert results[f"{metric}_mean"].between(0, 1).all()
        assert (results[f"{metric}_std"] >= 0).all()
    assert select_champion(results) == "rbf_svc"
    for pipeline in pipelines.values():
        assert set(pipeline.named_steps) == {"preprocessor", "classifier"}
        assert set(pipeline.predict(data[NUMERIC_FEATURES + CATEGORICAL_FEATURES])) <= {0, 1}
    report = format_report(results, select_champion(results))
    assert AUTHOR in report
    assert "rbf_svc" in report


def test_cv_means_and_sample_standard_deviations(data, evaluated):
    results, pipelines = evaluated
    scores = cross_validate(
        clone(pipelines["rbf_svc"]),
        data[NUMERIC_FEATURES + CATEGORICAL_FEATURES],
        data["num"],
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring=SCORING,
        error_score="raise",
    )
    row = results.set_index("model").loc["rbf_svc"]
    for metric in METRICS:
        assert row[f"{metric}_mean"] == pytest.approx(scores[f"test_{metric}"].mean())
        assert row[f"{metric}_std"] == pytest.approx(scores[f"test_{metric}"].std(ddof=1))


@pytest.mark.parametrize(
    ("recalls", "aucs", "precisions", "expected"),
    [
        ([0.9, 0.8], [0.7, 0.99], [0.7, 0.99], "a"),
        ([0.9, 0.9], [0.8, 0.9], [0.99, 0.7], "b"),
        ([0.9, 0.9], [0.9, 0.9], [0.7, 0.8], "b"),
        ([0.9, 0.9], [0.9, 0.9], [0.8, 0.8], "a"),
    ],
)
def test_champion_priority_and_stable_ties(recalls, aucs, precisions, expected):
    results = pd.DataFrame(
        {"model": ["a", "b"], "recall_mean": recalls,
         "roc_auc_mean": aucs, "precision_mean": precisions}
    )
    assert select_champion(results) == expected


def test_preprocessor_is_fit_only_on_training_rows_and_handles_unknowns(data):
    train = data.iloc[:200]
    holdout = data.iloc[200:].copy()
    holdout["age"] = 9999
    holdout["cp"] = 9999
    pipeline = build_pipeline(build_models()["logistic_regression"])
    pipeline.fit(train[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train["num"])
    preprocessor = pipeline.named_steps["preprocessor"]
    numeric = preprocessor.named_transformers_["numeric"]
    np.testing.assert_allclose(
        numeric.named_steps["imputer"].statistics_, train[NUMERIC_FEATURES].median()
    )
    categorical = preprocessor.named_transformers_["categorical"]
    assert 9999 not in categorical.named_steps["onehot"].categories_[1]
    assert pipeline.predict(holdout[NUMERIC_FEATURES + CATEGORICAL_FEATURES]).shape == (103,)
    np.testing.assert_allclose(
        numeric.named_steps["imputer"].statistics_, train[NUMERIC_FEATURES].median()
    )


@pytest.mark.parametrize("kind", ["missing-column", "empty", "invalid-target", "null-target"])
def test_reject_invalid_training_data(data, kind):
    invalid = data.copy()
    if kind == "missing-column":
        invalid = invalid.drop(columns="age")
    elif kind == "empty":
        invalid = invalid.iloc[:0]
    else:
        invalid.loc[0, "num"] = 2 if kind == "invalid-target" else np.nan
    with pytest.raises(ValueError, match="missing columns|empty|Target column"):
        evaluate_models(invalid)
