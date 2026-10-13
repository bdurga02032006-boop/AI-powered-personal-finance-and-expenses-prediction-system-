"""Load the selected model and create a forecast from local database history."""

from typing import Any

from database import database
from models.expense_model import ArtifactLoadError, load_artifact
from utils.preprocessing import build_next_month_features, finance_data_fingerprint


def predict_next_month() -> dict[str, Any]:
    artifact = load_artifact()
    if artifact is None:
        return {"ok": False, "message": "Train a model from at least nine months of expense history first."}
    income, expenses = database.get_income(), database.get_expenses()
    if artifact["data_fingerprint"] != finance_data_fingerprint(income, expenses):
        raise ArtifactLoadError(
            "Transactions changed after this model was trained. Retrain it from the Predictions page before forecasting."
        )
    inputs = build_next_month_features(expenses, income)
    if inputs is None:
        return {"ok": False, "message": "Not enough historical data to make a reliable prediction."}
    features, month = inputs
    expected_features = artifact["features"]
    missing_features = [name for name in expected_features if name not in features.columns]
    if missing_features:
        raise ArtifactLoadError(
            "The saved model expects unavailable input features. Retrain it from the Predictions page."
        )
    amount = max(0.0, float(artifact["model"].predict(features[expected_features])[0]))
    month_text = month.strftime("%Y-%m")
    database.save_prediction(month_text, amount, artifact["model_name"])
    return {"ok": True, "prediction_month": month_text, "predicted_amount": amount,
            "model_name": artifact["model_name"], "metrics": artifact["metrics"],
            "comparisons": artifact["comparisons"], "validation_months": artifact["validation_months"],
            "validation_actual": artifact["validation_actual"], "validation_predicted": artifact["validation_predicted"],
            "training_months": artifact["training_months"]}


def saved_prediction() -> dict[str, Any] | None:
    return predict_next_month() if load_artifact() is not None else None
