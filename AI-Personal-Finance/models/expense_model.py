"""Model definitions and artifact persistence."""

import logging
import pickle
from pathlib import Path
from typing import Any
import zlib

import joblib
import sklearn
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression


MODEL_PATH = Path(__file__).resolve().parent / "saved" / "expense_model.joblib"
logger = logging.getLogger(__name__)


class ArtifactLoadError(RuntimeError):
    """An existing prediction artifact cannot be used safely."""


def available_models() -> dict[str, Any]:
    return {
        "Linear Regression": LinearRegression(),
        "Random Forest Regressor": RandomForestRegressor(n_estimators=200, random_state=42),
        "Gradient Boosting Regressor": GradientBoostingRegressor(n_estimators=100, learning_rate=0.04, max_depth=2, random_state=42),
    }


def save_artifact(artifact: dict[str, Any], path: Path | None = None) -> None:
    path = MODEL_PATH if path is None else path
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, path)


def load_artifact(path: Path | None = None) -> dict[str, Any] | None:
    path = MODEL_PATH if path is None else path
    if not path.exists():
        return None
    try:
        artifact = joblib.load(path)
    except (OSError, ValueError, EOFError, pickle.UnpicklingError, ImportError,
            AttributeError, TypeError, IndexError, KeyError, zlib.error) as error:
        logger.exception("Unable to load prediction artifact at %s", path)
        raise ArtifactLoadError(
            "The saved prediction model is unreadable. Retrain it from the Predictions page."
        ) from error

    required_fields = {
        "model", "model_name", "features", "metrics", "comparisons",
        "validation_months", "validation_actual", "validation_predicted",
        "training_months", "versions", "data_fingerprint",
    }
    valid_artifact = (
        isinstance(artifact, dict)
        and required_fields.issubset(artifact)
        and isinstance(artifact["features"], list)
        and all(isinstance(feature, str) for feature in artifact["features"])
        and isinstance(artifact["metrics"], dict)
        and isinstance(artifact["comparisons"], list)
        and callable(getattr(artifact["model"], "predict", None))
        and isinstance(artifact["versions"], dict)
        and isinstance(artifact["data_fingerprint"], str)
    )
    if not valid_artifact:
        logger.error("Prediction artifact at %s is missing required fields or has an invalid format.", path)
        raise ArtifactLoadError(
            "The saved prediction model has an incompatible format. Retrain it from the Predictions page."
        )

    saved_sklearn_version = artifact["versions"].get("scikit_learn")
    if saved_sklearn_version != sklearn.__version__:
        logger.warning(
            "Prediction artifact at %s was created with scikit-learn %r; installed version is %s.",
            path, saved_sklearn_version, sklearn.__version__,
        )
        raise ArtifactLoadError(
            "The saved model was trained with a different scikit-learn version. Retrain it in this environment."
        )
    return artifact
