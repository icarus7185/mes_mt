"""Trains and serves the Usage_kWh regression model used to fill in
predicted values for tabular records forwarded from prod_line.
"""

import pickle
import warnings
from pathlib import Path

import pandas as pd
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBRegressor

warnings.filterwarnings("ignore")

COLUMN_RENAMES = {
    "Lagging_Current_Reactive.Power_kVarh": "Lagging_Reactive_Power_kVarh",
    "Leading_Current_Reactive_Power_kVarh": "Leading_Reactive_Power_kVarh",
    "Lagging_Current_Power_Factor": "Lagging_Power_Factor",
    "Leading_Current_Power_Factor": "Leading_Power_Factor",
    "CO2(tCO2)": "CO2",
}
TARGET_COLUMN = "Usage_kWh"
# 'date' identifies a record rather than predicting Usage_kWh, and records
# generated live carry timestamps never seen during training, so it's
# excluded from the feature set.
DROPPED_COLUMNS = ["date"]
DEFAULT_MODEL_PATH = Path("asst/data/model/analyst_model.pkl")


def _prepare_features(
    data: pd.DataFrame,
    feature_encoders: dict[str, LabelEncoder] | None = None,
) -> tuple[pd.DataFrame, dict[str, LabelEncoder]]:
    data = (
        data.rename(columns=COLUMN_RENAMES)
        .drop(columns=DROPPED_COLUMNS, errors="ignore")
        .copy()
    )
    encoders = feature_encoders or {}

    for column in data.select_dtypes(include="object").columns:
        if column not in encoders:
            encoders[column] = LabelEncoder()
            data[column] = encoders[column].fit_transform(data[column])
        else:
            data[column] = encoders[column].transform(data[column])

    return data, encoders


def train_model(
    training_csv_path: str | Path = "Steel_industry_data.csv",
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> dict[str, float | str]:
    """Train the Usage_kWh regression model and save its metadata."""
    data = pd.read_csv(training_csv_path).rename(columns=COLUMN_RENAMES)
    if TARGET_COLUMN not in data.columns:
        raise ValueError(f"Training CSV must contain the '{TARGET_COLUMN}' column")

    target = data.pop(TARGET_COLUMN)
    features, feature_encoders = _prepare_features(data)

    X_train, X_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.25,
        random_state=42,
    )

    model = XGBRegressor(random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    artifact = {
        "model": model,
        "feature_columns": list(features.columns),
        "feature_encoders": feature_encoders,
        "mse": mse,
        "r2": r2,
    }
    model_path = Path(model_path)
    model_path.parent.mkdir(parents=True, exist_ok=True)
    with model_path.open("wb") as file:
        pickle.dump(artifact, file)

    return {
        "mse": mse,
        "r2": r2,
        "model_path": str(model_path),
    }


def _load_artifact(model_path: str | Path) -> dict:
    model_path = Path(model_path)
    if not model_path.exists():
        raise FileNotFoundError(
            f"Saved model not found: {model_path}. Run train_model() first."
        )
    with model_path.open("rb") as file:
        return pickle.load(file)


def _predict_features(data: pd.DataFrame, artifact: dict) -> pd.Series:
    data = data.drop(columns=[TARGET_COLUMN], errors="ignore")
    expected_columns = artifact["feature_columns"]
    features, _ = _prepare_features(data, artifact["feature_encoders"])

    missing_columns = set(expected_columns) - set(features.columns)
    if missing_columns:
        raise ValueError(f"Record is missing columns: {sorted(missing_columns)}")

    return artifact["model"].predict(features[expected_columns])


def predict(
    csv_path: str | Path,
    model_path: str | Path = DEFAULT_MODEL_PATH,
) -> list[float]:
    """Predict Usage_kWh for each row of a CSV file using a saved model."""
    artifact = _load_artifact(model_path)
    data = pd.read_csv(csv_path).rename(columns=COLUMN_RENAMES)
    return _predict_features(data, artifact).tolist()


def predict_one(record: dict, model_path: str | Path = DEFAULT_MODEL_PATH) -> float:
    """Predict Usage_kWh for a single record (as sent live by prod_line)."""
    artifact = _load_artifact(model_path)
    data = pd.DataFrame([record]).rename(columns=COLUMN_RENAMES)
    prediction = _predict_features(data, artifact)[0]
    return float(prediction)
