"""Model definitions and artifact persistence."""

from pathlib import Path
from typing import Any

import joblib
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression


MODEL_PATH = Path(__file__).resolve().parent / "saved" / "expense_model.joblib"


def available_models() -> dict[str, Any]:
    return {
        "Linear Regression": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=200, min_samples_leaf=1, random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, learning_rate=0.04, max_depth=2, random_state=42),
    }


def save_artifact(artifact: dict[str, Any], path: Path = MODEL_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)


def load_artifact(path: Path = MODEL_PATH) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return joblib.load(path)
    except (OSError, ValueError, EOFError):
        return None
