"""Pandas-based reporting calculations shared by dashboard and analytics."""

from datetime import date
import math

import pandas as pd

from utils.helpers import finance_summary
from utils.preprocessing import clean_transactions


def category_summary(expenses: pd.DataFrame) -> pd.DataFrame:
    if expenses.empty:
        return pd.DataFrame(columns=["category", "amount", "percentage"])
    cleaned = clean_transactions(expenses, "expense_date")
    totals = cleaned.groupby("category", as_index=False)["amount"].sum()
    total = float(totals["amount"].sum())
    totals["percentage"] = totals["amount"].div(total).mul(100) if total else 0.0
    return totals.sort_values("amount", ascending=False, ignore_index=True)


def monthly_summary(income: pd.DataFrame, expenses: pd.DataFrame) -> pd.DataFrame:
    frames = []
    if not income.empty:
        frame = clean_transactions(income, "income_date")
        frame["month"] = frame["income_date"].dt.to_period("M").dt.to_timestamp()
        frames.append(frame.groupby("month")["amount"].sum().rename("income"))
    if not expenses.empty:
        frame = clean_transactions(expenses, "expense_date")
        frame["month"] = frame["expense_date"].dt.to_period("M").dt.to_timestamp()
        frames.append(frame.groupby("month")["amount"].sum().rename("expenses"))
    if not frames:
        return pd.DataFrame(columns=["month", "income", "expenses", "savings", "expense_growth"])
    monthly = pd.concat(frames, axis=1).fillna(0).sort_index()
    for column in ("income", "expenses"):
        if column not in monthly.columns:
            monthly[column] = 0.0
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
    result = budgets.merge(actual, on="category", how="left")
    result["actual_expense"] = result["actual_expense"].fillna(0.0).astype(float)
    result["remaining_budget"] = result["budget_amount"] - result["actual_expense"]
    result["utilization"] = result["actual_expense"].div(result["budget_amount"]).mul(100)
    result["exceeded_amount"] = (-result["remaining_budget"]).clip(lower=0)
    result["status"] = result["utilization"].map(lambda x: "Budget Exceeded" if x >= 100 else "Near Limit" if x >= 85 else "Approaching Limit" if x >= 70 else "Under Budget")
    result["indicator"] = result["status"].map({"Under Budget": "🟢", "Approaching Limit": "🟡", "Near Limit": "🟠", "Budget Exceeded": "🔴"})
    return result[columns]


def financial_alerts(income: pd.DataFrame, expenses: pd.DataFrame, budgets: pd.DataFrame,
                     month: str, low_balance_threshold: float = 0.0,
                     as_of: date | None = None) -> list[dict[str, str]]:
    """Return alerts supported by recorded cash flow, budgets, and complete history."""
    if not math.isfinite(low_balance_threshold) or low_balance_threshold < 0:
        raise ValueError("Low balance threshold must be a finite, non-negative amount.")

    alerts: list[dict[str, str]] = []
    totals = finance_summary(income, expenses)
    has_transactions = not income.empty or not expenses.empty
    if has_transactions and totals["savings"] < low_balance_threshold:
        alerts.append({
            "severity": "warning",
            "message": f"Recorded net balance is ₹{totals['savings']:,.2f}, below your ₹{low_balance_threshold:,.2f} alert threshold.",
        })

    month_income = 0.0
    if not income.empty:
        clean_income = clean_transactions(income, "income_date")
        month_income = float(clean_income.loc[
            clean_income["income_date"].dt.strftime("%Y-%m").eq(month), "amount"
        ].sum())
    month_expenses = current_month_expense(expenses, month)
    if month_expenses > month_income:
        alerts.append({
            "severity": "error",
            "message": f"This month's expenses exceed recorded income by ₹{month_expenses - month_income:,.2f}.",
        })

    status = budget_status(budgets, expenses, month)
    for row in status.loc[status["utilization"].ge(70)].itertuples(index=False):
        severity = "error" if row.utilization >= 100 else "warning"
        if row.utilization >= 100:
            message = f"{row.category} is over budget by ₹{row.exceeded_amount:,.2f}."
        else:
            message = f"{row.category} has used {row.utilization:.0f}% of its ₹{row.budget_amount:,.2f} budget."
        alerts.append({"severity": severity, "message": message})

    if not expenses.empty:
        clean_expenses = clean_transactions(expenses, "expense_date")
        month_totals = clean_expenses.groupby(
            clean_expenses["expense_date"].dt.to_period("M")
        )["amount"].sum()
        current_period = pd.Period(as_of or date.today(), freq="M")
        last_completed_period = current_period - 1
        baseline_periods = [last_completed_period - offset for offset in range(1, 7)]
        if last_completed_period in month_totals.index and all(
            period in month_totals.index for period in baseline_periods
        ):
            baseline = pd.Series([float(month_totals[period]) for period in baseline_periods])
            historical_mean = float(baseline.mean())
            historical_std = float(baseline.std(ddof=0))
            latest_complete = float(month_totals[last_completed_period])
            if latest_complete > historical_mean + 2 * historical_std:
                alerts.append({
                    "severity": "warning",
                    "message": (
                        f"Recorded spending in {last_completed_period} was unusually high: "
                        f"₹{latest_complete:,.2f}, above the six-month baseline of ₹{historical_mean:,.2f}."
                    ),
                })
        else:
            alerts.append({
                "severity": "info",
                "message": "Unusual-spending checks need expenses in the last seven complete months; there is not enough history yet.",
            })
    return alerts
