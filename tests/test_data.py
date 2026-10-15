from io import BytesIO

import pandas as pd
import pytest

from src.data import download_heart
from src.data.prepare import COLUMNS, RAW_PATH, load_raw_data, prepare_dataframe, prepare_file


def test_source_schema_missingness_and_binary_target(data):
    raw = load_raw_data()
    assert raw.shape == (303, 14)
    assert list(raw.columns) == COLUMNS
    assert data["num"].value_counts().to_dict() == {0: 164, 1: 139}
    assert data.isna().sum().loc[["ca", "thal"]].to_dict() == {"ca": 4, "thal": 2}
    assert data.isna().sum().sum() == 6
    assert all(pd.api.types.is_numeric_dtype(dtype) for dtype in data.dtypes)
    pd.testing.assert_frame_equal(data.drop(columns="num"), raw.drop(columns="num"))


def test_binarization_preserves_input():
    raw = pd.DataFrame({"num": [0, 1, 2, 3, 4], "age": [40] * 5})
    original = raw.copy(deep=True)
    assert prepare_dataframe(raw)["num"].tolist() == [0, 1, 1, 1, 1]
    pd.testing.assert_frame_equal(raw, original)


@pytest.mark.parametrize("target", ["?", "-1", "5", "1.5"])
def test_raw_invalid_target(tmp_path, target):
    row = RAW_PATH.read_text().splitlines()[0].split(",")
    row[-1] = target
    source = tmp_path / "invalid.data"
    source.write_text(",".join(row) + "\n")
    with pytest.raises(ValueError, match="Target column"):
        load_raw_data(source)


def test_prepare_file_round_trip(tmp_path, data):
    destination = tmp_path / "processed" / "heart.csv"
    assert prepare_file(RAW_PATH, destination) == destination
    pd.testing.assert_frame_equal(pd.read_csv(destination), data)


def test_download_writes_validated_source_and_attribution(tmp_path, monkeypatch):
    source = RAW_PATH.read_bytes()
    monkeypatch.setattr(download_heart, "urlopen", lambda *args, **kwargs: BytesIO(source))
    monkeypatch.setattr(download_heart, "RAW_PATH", tmp_path / "raw" / "heart.data")
    monkeypatch.setattr(download_heart, "POINTER_PATH", tmp_path / "raw" / "README.md")
    assert download_heart.download_dataset().read_bytes() == source
    pointer = download_heart.POINTER_PATH.read_text()
    assert download_heart.AUTHOR in pointer
    assert download_heart.DATASET_URL in pointer


@pytest.mark.parametrize("content", [b"", b"1,2,3\n"])
def test_download_rejects_bad_shape_before_writing(tmp_path, monkeypatch, content):
    monkeypatch.setattr(download_heart, "urlopen", lambda *args, **kwargs: BytesIO(content))
    monkeypatch.setattr(download_heart, "RAW_PATH", tmp_path / "heart.data")
    with pytest.raises(ValueError, match="Unexpected dataset shape"):
        download_heart.download_dataset()
    assert not download_heart.RAW_PATH.exists()
