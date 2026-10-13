"""Shared categories, validation, and financial summary helpers."""

from datetime import date
import math
from typing import Any

import pandas as pd


CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Entertainment", "Healthcare", "Education", "Rent", "Others"]
PAYMENT_METHODS = ["Cash", "UPI", "Debit Card", "Credit Card", "Bank Transfer", "Other"]


def validate_amount(value: Any, label: str = "Amount") -> float:
    try:
        amount = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a valid number.") from exc
    if not math.isfinite(amount) or amount <= 0:
        raise ValueError(f"{label} must be greater than zero.")
    return amount


def validate_text(value: str, label: str, max_length: int = 120) -> str:
    cleaned = str(value).strip()
    if not cleaned:
        raise ValueError(f"{label} is required.")
    if len(cleaned) > max_length:
        raise ValueError(f"{label} must be {max_length} characters or fewer.")
    return cleaned


def validate_date(value: date) -> str:
    if value > date.today():
        raise ValueError("Transaction date cannot be in the future.")
    return value.isoformat()


def finance_summary(income: pd.DataFrame, expenses: pd.DataFrame) -> dict[str, float]:
    income_total = float(income["amount"].sum()) if not income.empty else 0.0
    expense_total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
    savings = income_total - expense_total
    return {"income": income_total, "expenses": expense_total, "savings": savings,
            "savings_percentage": (savings / income_total * 100) if income_total > 0 else 0.0}
