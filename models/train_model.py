"""Time-aware comparison and training for next-month expense prediction."""

from math import ceil, sqrt
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from database import database
from models.expense_model import available_models, save_artifact
from utils.preprocessing import build_feature_frame


MINIMUM_MONTHS = 9


def train_and_compare(
    expenses: pd.DataFrame | None = None,
    income: pd.DataFrame | None = None,
    save: bool = True,
) -> dict[str, Any]:
    expenses = database.get_expenses() if expenses is None else expenses
    income = database.get_income() if income is None else income
    if expenses.empty:
        return {"ok": False, "message": "Not enough historical data to make a reliable prediction."}
    parsed_dates = pd.to_datetime(expenses["expense_date"], errors="coerce").dropna()
    month_count = parsed_dates.dt.to_period("M").nunique()
    features, targets, months = build_feature_frame(expenses, income)
    if month_count < MINIMUM_MONTHS or len(features) < 6:
        return {"ok": False, "message": "Not enough historical data to make a reliable prediction."}

    test_size = max(2, ceil(len(features) * 0.25))
    split_at = len(features) - test_size
    if split_at < 4:
        return {"ok": False, "message": "Not enough historical data to make a reliable prediction."}
    x_train, x_test = features.iloc[:split_at], features.iloc[split_at:]
    y_train, y_test = targets.iloc[:split_at], targets.iloc[split_at:]
    comparisons: list[dict[str, Any]] = []
    best: tuple[float, str, Any, np.ndarray] | None = None
    for name, estimator in available_models().items():
        estimator.fit(x_train, y_train)
        predicted = estimator.predict(x_test)
        mae = float(mean_absolute_error(y_test, predicted))
        rmse = float(sqrt(mean_squared_error(y_test, predicted)))
        r2 = float(r2_score(y_test, predicted))
        comparisons.append({"model_name": name, "mae": mae, "rmse": rmse, "r2": r2})
        candidate = (rmse, name, estimator, predicted)
        if best is None or candidate[0] < best[0]:
            best = candidate

    assert best is not None
    _, selected_name, _, validation_predictions = best
    final_model = available_models()[selected_name]
    final_model.fit(features, targets)
    metrics = next(row for row in comparisons if row["model_name"] == selected_name)
    artifact = {
        "model": final_model,
        "model_name": selected_name,
        "features": list(features.columns),
        "metrics": metrics,
        "comparisons": comparisons,
        "validation_months": [month.strftime("%Y-%m") for month in months[split_at:]],
        "validation_actual": y_test.astype(float).tolist(),
        "validation_predicted": [float(value) for value in validation_predictions],
        "training_months": int(month_count),
    }
    if save:
        save_artifact(artifact)
    return {"ok": True, **artifact}
