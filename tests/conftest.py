import json

import pytest

from src.data.prepare import RAW_PATH, load_raw_data, prepare_dataframe
from src.train import package as packaging
from src.train.train import ROOT, evaluate_models


@pytest.fixture(scope="session")
def data():
    return prepare_dataframe(load_raw_data(RAW_PATH))


@pytest.fixture(scope="session")
def evaluated(data):
    return evaluate_models(data)


@pytest.fixture(scope="session")
def packaged(tmp_path_factory, data):
    directory = tmp_path_factory.mktemp("packaged")
    source = directory / "heart.csv"
    data.to_csv(source, index=False)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(packaging, "MODEL_PATH", directory / "heart_pipeline.joblib")
        patch.setattr(packaging, "CALIBRATION_REPORT", directory / "calibration_summary.md")
        patch.setattr(packaging, "RELIABILITY_PATH", directory / "calibration_reliability.png")
        metrics = packaging.package(source)
    return directory, metrics


@pytest.fixture
def records():
    return json.loads((ROOT / "examples" / "patient.json").read_text())
