import pandas as pd
import plotly.express as px
import streamlit as st

from analysis.spending_analysis import budget_status, category_summary, monthly_summary
from database import database
from models.expense_model import load_artifact
from utils.helpers import finance_summary


def render() -> None:
    st.title("Personal Finance Dashboard")
    st.caption("A clear view of your recorded income, spending, and savings.")
    income, expenses = database.get_income(), database.get_expenses()
    summary = finance_summary(income, expenses)
    first, second, third, fourth = st.columns(4)
    first.metric("Total income", f"₹{summary['income']:,.2f}")
    second.metric("Total expenses", f"₹{summary['expenses']:,.2f}")
    third.metric("Current savings", f"₹{summary['savings']:,.2f}")
    fourth.metric("Savings percentage", f"{summary['savings_percentage']:.1f}%")

    artifact = load_artifact()
    latest_prediction = database.get_latest_prediction()
    prediction_amount = latest_prediction["predicted_amount"] if latest_prediction else None
    if artifact and latest_prediction is None:
        st.info("A trained model is available. Open Predictions and run a forecast to record next month's estimate.")
    st.metric("Predicted next month expense", f"₹{prediction_amount:,.2f}" if prediction_amount is not None else "Not available")

    monthly = monthly_summary(income, expenses)
    categories = category_summary(expenses)
    if monthly.empty and categories.empty:
        st.info("Add income and expenses to populate your dashboard charts.")
    else:
        left, right = st.columns(2)
        with left:
            if not monthly.empty:
                st.plotly_chart(px.line(monthly, x="month", y="expenses", markers=True, title="Monthly Expense Trend"), use_container_width=True)
            if not monthly.empty:
                st.plotly_chart(px.bar(monthly, x="month", y=["income", "expenses"], barmode="group", title="Income vs Expense"), use_container_width=True)
        with right:
            if not categories.empty:
                st.plotly_chart(px.pie(categories, names="category", values="amount", hole=0.52, title="Category-wise Expense Distribution"), use_container_width=True)
            if not monthly.empty:
                st.plotly_chart(px.area(monthly, x="month", y="savings", markers=True, title="Savings Trend"), use_container_width=True)

    left, right = st.columns(2)
    with left:
        st.subheader("Recent transactions")
        transactions = database.get_transactions().head(8)
        if transactions.empty:
            st.caption("No transactions recorded yet.")
        else:
            st.dataframe(transactions, hide_index=True, use_container_width=True)
    with right:
        st.subheader("Budget alerts")
        month = pd.Timestamp.today().strftime("%Y-%m")
        alerts = budget_status(database.get_budgets(month), expenses, month)
        if alerts.empty:
            st.caption("No budgets are set for this month.")
        else:
            exceeded = alerts[alerts["status"].eq("Budget Exceeded")]
            approaching = alerts[alerts["status"].isin(["Near Limit", "Approaching Limit"])]
            if exceeded.empty and approaching.empty:
                st.success("All current budgets are under their alert thresholds.")
            for _, alert in pd.concat([exceeded, approaching]).iterrows():
                st.warning(f"{alert['indicator']} {alert['category']}: {alert['status']} ({alert['utilization']:.0f}% used)")
