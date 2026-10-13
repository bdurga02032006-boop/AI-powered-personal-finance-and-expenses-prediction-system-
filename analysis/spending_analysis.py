"""Pandas-based reporting calculations shared by the dashboard and analytics pages."""

import pandas as pd

from utils.preprocessing import clean_transactions


def category_summary(expenses: pd.DataFrame) -> pd.DataFrame:
    if expenses.empty:
        return pd.DataFrame(columns=["category", "amount", "percentage"])
    cleaned = clean_transactions(expenses, "expense_date")
    totals = cleaned.groupby("category", as_index=False)["amount"].sum().rename(columns={"amount": "amount"})
    total = float(totals["amount"].sum())
    totals["percentage"] = totals["amount"].div(total).mul(100) if total else 0.0
    return totals.sort_values("amount", ascending=False, ignore_index=True)


def monthly_summary(income: pd.DataFrame, expenses: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if not income.empty:
        current = clean_transactions(income, "income_date")
        current = current.assign(month=current["income_date"].dt.to_period("M").dt.to_timestamp())
        frames.append(current.groupby("month")["amount"].sum().rename("income"))
    if not expenses.empty:
        current = clean_transactions(expenses, "expense_date")
        current = current.assign(month=current["expense_date"].dt.to_period("M").dt.to_timestamp())
        frames.append(current.groupby("month")["amount"].sum().rename("expenses"))
    if not frames:
        return pd.DataFrame(columns=["month", "income", "expenses", "savings", "expense_growth"])
    monthly = pd.concat(frames, axis=1).fillna(0).sort_index()
    monthly["savings"] = monthly["income"] - monthly["expenses"]
    monthly["expense_growth"] = monthly["expenses"].pct_change().mul(100).replace([float("inf"), -float("inf")], pd.NA)
    return monthly.rename_axis("month").reset_index()


def current_month_expense(expenses: pd.DataFrame, month: str) -> float:
    if expenses.empty:
        return 0.0
    cleaned = clean_transactions(expenses, "expense_date")
    return float(cleaned.loc[cleaned["expense_date"].dt.strftime("%Y-%m").eq(month), "amount"].sum())


def budget_status(budgets: pd.DataFrame, expenses: pd.DataFrame, month: str) -> pd.DataFrame:
    columns = ["category", "budget_amount", "actual_expense", "remaining_budget", "utilization", "exceeded_amount", "status", "indicator"]
    if budgets.empty:
        return pd.DataFrame(columns=columns)
    actual = pd.DataFrame(columns=["category", "actual_expense"])
    if not expenses.empty:
        cleaned = clean_transactions(expenses, "expense_date")
        selected = cleaned.loc[cleaned["expense_date"].dt.strftime("%Y-%m").eq(month)]
        actual = selected.groupby("category", as_index=False)["amount"].sum().rename(columns={"amount": "actual_expense"})
    result = budgets.merge(actual, on="category", how="left").fillna({"actual_expense": 0})
    result["remaining_budget"] = result["budget_amount"] - result["actual_expense"]
    result["utilization"] = result["actual_expense"].div(result["budget_amount"]).mul(100)
    result["exceeded_amount"] = (-result["remaining_budget"]).clip(lower=0)
    result["status"] = result["utilization"].map(
        lambda value: "Budget Exceeded" if value >= 100 else "Near Limit" if value >= 85 else "Approaching Limit" if value >= 70 else "Under Budget"
    )
    result["indicator"] = result["status"].map(
        {"Under Budget": "🟢", "Approaching Limit": "🟡", "Near Limit": "🟠", "Budget Exceeded": "🔴"}
    )
    return result[columns]
