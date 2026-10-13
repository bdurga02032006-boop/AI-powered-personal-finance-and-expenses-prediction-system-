"""Load the selected trained model and create a database-grounded forecast."""

from typing import Any

from database import database
from models.expense_model import load_artifact
from utils.preprocessing import build_next_month_features


def predict_next_month() -> dict[str, Any]:
    artifact = load_artifact()
    if artifact is None:
        return {"ok": False, "message": "Train a model from at least nine months of expense history first."}
    expenses = database.get_expenses()
    income = database.get_income()
    inputs = build_next_month_features(expenses, income)
    if inputs is None:
        return {"ok": False, "message": "Not enough historical data to make a reliable prediction."}
    features, month = inputs
    amount = max(0.0, float(artifact["model"].predict(features[artifact["features"]])[0]))
    database.save_prediction(month.strftime("%Y-%m"), amount, artifact["model_name"])
    return {
        "ok": True,
        "prediction_month": month.strftime("%Y-%m"),
        "predicted_amount": amount,
        "model_name": artifact["model_name"],
        "metrics": artifact["metrics"],
        "comparisons": artifact["comparisons"],
        "validation_months": artifact["validation_months"],
        "validation_actual": artifact["validation_actual"],
        "validation_predicted": artifact["validation_predicted"],
        "training_months": artifact["training_months"],
    }


def saved_prediction() -> dict[str, Any] | None:
    artifact = load_artifact()
    if artifact is None:
        return None
    return predict_next_month()
