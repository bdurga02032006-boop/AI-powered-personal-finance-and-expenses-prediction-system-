"""Time-aware comparison and training for next-month expense prediction."""

from math import ceil, sqrt
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from database import database
from models.expense_model import available_models, save_artifact
from utils.preprocessing import build_feature_frame, finance_data_fingerprint


MINIMUM_MONTHS = 9


def train_and_compare(expenses: pd.DataFrame | None = None, income: pd.DataFrame | None = None,
                      save: bool = True) -> dict[str, Any]:
    expenses = database.get_expenses() if expenses is None else expenses
    income = database.get_income() if income is None else income
    if expenses.empty:
        return {"ok": False, "message": "Not enough historical data to make a reliable prediction."}
    distinct_months = pd.to_datetime(expenses["expense_date"], errors="coerce").dropna().dt.to_period("M").nunique()
    features, targets, months = build_feature_frame(expenses, income)
    if distinct_months < MINIMUM_MONTHS or len(features) < 6:
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
        row = {"model_name": name, "mae": float(mean_absolute_error(y_test, predicted)),
               "rmse": float(sqrt(mean_squared_error(y_test, predicted))), "r2": float(r2_score(y_test, predicted))}
        comparisons.append(row)
        if best is None or row["rmse"] < best[0]:
            best = (row["rmse"], name, estimator, predicted)

    assert best is not None
    _, selected_name, _, validation_predictions = best
    final_model = available_models()[selected_name]
    final_model.fit(features, targets)
    metrics = next(row for row in comparisons if row["model_name"] == selected_name)
    artifact = {
        "model": final_model, "model_name": selected_name, "features": list(features.columns),
        "metrics": metrics, "comparisons": comparisons,
        "validation_months": [month.strftime("%Y-%m") for month in months[split_at:]],
        "validation_actual": y_test.astype(float).tolist(),
        "validation_predicted": [float(value) for value in validation_predictions],
        "training_months": int(distinct_months),
        "versions": {"scikit_learn": sklearn.__version__, "joblib": joblib.__version__},
        "data_fingerprint": finance_data_fingerprint(income, expenses),
    }
    if save:
        save_artifact(artifact)
    return {"ok": True, **artifact}
