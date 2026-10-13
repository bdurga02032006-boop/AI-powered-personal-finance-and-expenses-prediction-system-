"""Reusable cleaning and feature-building functions for finance data."""

from __future__ import annotations

from hashlib import sha256
import json

import pandas as pd

from utils.helpers import CATEGORIES


def finance_data_fingerprint(income: pd.DataFrame, expenses: pd.DataFrame) -> str:
    """Hash only the dates and values used by the expense model, preserving duplicate rows."""
    clean_income = clean_transactions(income, "income_date", duplicate_columns=[])
    clean_expenses = clean_transactions(expenses, "expense_date", duplicate_columns=[])
    income_rows = sorted(
        (row.income_date.strftime("%Y-%m-%d"), format(float(row.amount), ".17g"))
        for row in clean_income.itertuples(index=False)
    )
    expense_rows = sorted(
        (row.expense_date.strftime("%Y-%m-%d"), str(row.category), format(float(row.amount), ".17g"))
        for row in clean_expenses.itertuples(index=False)
    )
    payload = json.dumps({"income": income_rows, "expenses": expense_rows}, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _feature_category_name(category: str) -> str:
    return "other" if category == "Others" else category.lower()


def clean_transactions(frame: pd.DataFrame, date_column: str, amount_column: str = "amount",
                       duplicate_columns: list[str] | None = None) -> pd.DataFrame:
    """Convert dates and amounts, remove incomplete/invalid rows and duplicates."""
    if frame.empty:
        return frame.copy()
    cleaned = frame.copy()
    cleaned[date_column] = pd.to_datetime(cleaned[date_column], errors="coerce")
    cleaned[amount_column] = pd.to_numeric(cleaned[amount_column], errors="coerce")
    cleaned = cleaned.dropna(subset=[date_column, amount_column])
    cleaned = cleaned[cleaned[amount_column].gt(0)].copy()
    columns = [column for column in (duplicate_columns or list(cleaned.columns)) if column in cleaned.columns]
    if columns:
        cleaned = cleaned.drop_duplicates(subset=columns)
    return cleaned.reset_index(drop=True)


def monthly_aggregation(frame: pd.DataFrame, date_column: str, amount_column: str = "amount") -> pd.Series:
    cleaned = clean_transactions(frame, date_column, amount_column)
    if cleaned.empty:
        return pd.Series(dtype=float, name="total_expense")
    values = cleaned.groupby(cleaned[date_column].dt.to_period("M"))[amount_column].sum().sort_index()
    values.index = values.index.to_timestamp()
    return values.astype(float).rename("total_expense")


def _monthly_tables(expenses: pd.DataFrame, income: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    clean_expenses = clean_transactions(expenses, "expense_date")
    clean_income = clean_transactions(income, "income_date")
    if clean_expenses.empty:
        return pd.DataFrame(), pd.Series(dtype=float)
    first = clean_expenses["expense_date"].min().to_period("M")
    last = clean_expenses["expense_date"].max().to_period("M")
    months = pd.period_range(first, last, freq="M")
    monthly = pd.DataFrame(0.0, index=months, columns=CATEGORIES)
    totals = clean_expenses.pivot_table(index=clean_expenses["expense_date"].dt.to_period("M"),
                                        columns="category", values="amount", aggfunc="sum", fill_value=0)
    for category in CATEGORIES:
        if category in totals.columns:
            monthly[category] = totals[category].reindex(months, fill_value=0).astype(float)
    monthly["total_expense"] = monthly[CATEGORIES].sum(axis=1)
    if clean_income.empty:
        income_monthly = pd.Series(0.0, index=months)
    else:
        income_monthly = clean_income.groupby(clean_income["income_date"].dt.to_period("M"))["amount"].sum()
        income_monthly = income_monthly.reindex(months, fill_value=0).astype(float)
    return monthly, income_monthly


def build_feature_frame(expenses: pd.DataFrame, income: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.DatetimeIndex]:
    """Create leakage-safe features from the three months preceding each target month."""
    monthly, income_monthly = _monthly_tables(expenses, income)
    feature_names = ["previous_month_expense", "previous_2_month_expense", "previous_3_month_average",
                     "monthly_income", *[f"{_feature_category_name(c)}_expense" for c in CATEGORIES], "month_number"]
    if monthly.empty or len(monthly) < 4:
        return pd.DataFrame(columns=feature_names), pd.Series(dtype=float, name="next_month_total_expense"), pd.DatetimeIndex([])
    rows, targets, target_months = [], [], []
    for target_index in range(3, len(monthly)):
        source_index = target_index - 1
        source = monthly.iloc[source_index]
        target_month = monthly.index[target_index].to_timestamp()
        row = {
            "previous_month_expense": float(source["total_expense"]),
            "previous_2_month_expense": float(monthly.iloc[target_index - 2]["total_expense"]),
            "previous_3_month_average": float(monthly.iloc[target_index - 3:target_index]["total_expense"].mean()),
            "monthly_income": float(income_monthly.iloc[source_index]),
            "month_number": float(target_month.month),
        }
        row.update({f"{_feature_category_name(c)}_expense": float(source[c]) for c in CATEGORIES})
        rows.append(row)
        targets.append(float(monthly.iloc[target_index]["total_expense"]))
        target_months.append(target_month)
    return pd.DataFrame(rows, columns=feature_names), pd.Series(targets, name="next_month_total_expense", dtype=float), pd.DatetimeIndex(target_months)


def build_next_month_features(expenses: pd.DataFrame, income: pd.DataFrame) -> tuple[pd.DataFrame, pd.Timestamp] | None:
    monthly, income_monthly = _monthly_tables(expenses, income)
    if monthly.empty or len(monthly) < 3:
        return None
    source = monthly.iloc[-1]
    target_month = (monthly.index[-1] + 1).to_timestamp()
    row = {
        "previous_month_expense": float(source["total_expense"]),
        "previous_2_month_expense": float(monthly.iloc[-2]["total_expense"]),
        "previous_3_month_average": float(monthly.iloc[-3:]["total_expense"].mean()),
        "monthly_income": float(income_monthly.iloc[-1]),
        "month_number": float(target_month.month),
    }
    row.update({f"{_feature_category_name(c)}_expense": float(source[c]) for c in CATEGORIES})
    return pd.DataFrame([row]), target_month
