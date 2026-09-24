import pickle
from pathlib import Path

import pandas as pd
import pytest

from asst.services.analyst_service import (
    _prepare_features,
    predict,
    predict_one,
    train_model,
)


@pytest.fixture(scope="module")
def model_path(steel_csv: Path, tmp_path_factory: pytest.TempPathFactory) -> Path:
    path = tmp_path_factory.mktemp("model") / "analyst_model.pkl"
    train_model(steel_csv, path)
    return path


def test_train_model_reports_metrics_and_saves_artifact(
    steel_csv: Path, tmp_path: Path
) -> None:
    path = tmp_path / "model" / "analyst_model.pkl"

    result = train_model(steel_csv, path)

    assert set(result) == {"mse", "r2", "model_path"}
    assert result["model_path"] == str(path)
    assert path.is_file()


def test_artifact_holds_model_features_and_encoders(model_path: Path) -> None:
    with model_path.open("rb") as file:
        artifact = pickle.load(file)

    assert {"model", "feature_columns", "feature_encoders", "mse", "r2"} <= set(artifact)
    assert "date" not in artifact["feature_columns"]
    assert "Usage_kWh" not in artifact["feature_columns"]
    assert "CO2" in artifact["feature_columns"]
    assert "Lagging_Reactive_Power_kVarh" in artifact["feature_columns"]
    assert set(artifact["feature_encoders"]) == {"WeekStatus", "Day_of_week", "Load_Type"}


def test_train_model_requires_target_column(steel_csv: Path, tmp_path: Path) -> None:
    csv_path = tmp_path / "no_target.csv"
    pd.read_csv(steel_csv).drop(columns=["Usage_kWh"]).to_csv(csv_path, index=False)

    with pytest.raises(ValueError, match="Usage_kWh"):
        train_model(csv_path, tmp_path / "model.pkl")


def test_predict_one_returns_a_float(model_path: Path, sample_record: dict) -> None:
    prediction = predict_one(sample_record, model_path)

    assert isinstance(prediction, float)


def test_predict_one_ignores_the_date(model_path: Path, sample_record: dict) -> None:
    other_date = dict(sample_record, date="31/12/2030 23:59:59")

    assert predict_one(sample_record, model_path) == predict_one(other_date, model_path)


def test_predict_returns_one_value_per_row(model_path: Path, steel_csv: Path) -> None:
    predictions = predict(steel_csv, model_path)

    assert len(predictions) == len(pd.read_csv(steel_csv))


def test_predict_one_without_model_raises(tmp_path: Path, sample_record: dict) -> None:
    with pytest.raises(FileNotFoundError, match="train_model"):
        predict_one(sample_record, tmp_path / "missing.pkl")


def test_predict_one_with_missing_feature_raises(
    model_path: Path, sample_record: dict
) -> None:
    del sample_record["NSM"]

    with pytest.raises(ValueError, match="NSM"):
        predict_one(sample_record, model_path)


def test_predict_one_with_unseen_category_raises(
    model_path: Path, sample_record: dict
) -> None:
    sample_record["Load_Type"] = "Unknown_Load"

    with pytest.raises(ValueError):
        predict_one(sample_record, model_path)


def test_prepare_features_reuses_fitted_encoders() -> None:
    training = pd.DataFrame(
        {"date": ["a", "b"], "CO2(tCO2)": [0.1, 0.2], "Load_Type": ["Light_Load", "Maximum_Load"]}
    )
    live = pd.DataFrame({"date": ["c"], "CO2(tCO2)": [0.3], "Load_Type": ["Maximum_Load"]})

    fitted, encoders = _prepare_features(training)
    transformed, _ = _prepare_features(live, encoders)

    assert list(fitted.columns) == ["CO2", "Load_Type"]
    assert transformed["Load_Type"].iloc[0] == fitted["Load_Type"].iloc[1]
