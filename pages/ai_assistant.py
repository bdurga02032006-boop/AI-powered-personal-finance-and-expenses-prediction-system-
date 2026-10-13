from datetime import date
from typing import Any

import streamlit as st

from ai.financial_assistant import OLLAMA_UNAVAILABLE, generate_financial_response
from analysis.spending_analysis import budget_status
from database import database
from models.expense_model import load_artifact
from prediction.expense_predictor import predict_next_month
from utils.helpers import finance_summary


def _context() -> dict[str, Any]:
    income, expenses = database.get_income(), database.get_expenses()
    summary = finance_summary(income, expenses)
    categories = (
        expenses.groupby("category")["amount"].sum().sort_values(ascending=False).to_dict()
        if not expenses.empty else {}
    )
    current_month = date.today().strftime("%Y-%m")
    budgets = budget_status(database.get_budgets(current_month), expenses, current_month)
    budget_records = budgets[["category", "budget_amount", "actual_expense", "remaining_budget", "utilization", "status"]].to_dict("records") if not budgets.empty else []
    prediction: dict[str, Any] | None = None
    if load_artifact() is not None:
        result = predict_next_month()
        if result["ok"]:
            prediction = {"month": result["prediction_month"], "amount": result["predicted_amount"], "model": result["model_name"]}
    return {
        **summary,
        "category_totals": categories,
        "budget_status": budget_records,
        "ml_prediction": prediction,
        "currency": "INR",
        "data_scope": "Recorded local transactions only; aggregated totals, no names or descriptions.",
    }


def render() -> None:
    st.title("AI Financial Assistant")
    st.caption("Private local analysis using Ollama. Only calculated summaries are sent to the local model.")
    question = st.text_area("Ask about your finances", placeholder="Where am I spending the most?", max_chars=1000)
    if st.button("Ask assistant", type="primary"):
        answer, error = generate_financial_response(_context(), question)
        if error:
            if error == OLLAMA_UNAVAILABLE:
                st.warning(OLLAMA_UNAVAILABLE)
            else:
                st.info(error)
        elif answer:
            st.markdown(answer)
