from datetime import date

import streamlit as st

from analysis.spending_analysis import budget_status
from database import database
from utils.helpers import CATEGORIES, validate_amount


def render() -> None:
    st.title("Monthly Budget Planner")
    month = st.date_input("Budget month", value=date.today().replace(day=1), key="budget_month").strftime("%Y-%m")
    with st.form("set_budget", clear_on_submit=True):
        category = st.selectbox("Category", CATEGORIES)
        amount = st.number_input("Budget amount (₹)", min_value=0.01, step=500.0, format="%.2f")
        submitted = st.form_submit_button("Save monthly budget", type="primary")
    if submitted:
        try:
            database.save_budget(category, month, validate_amount(amount, "Budget amount"))
            st.success("Budget saved for the selected month.")
            st.rerun()
        except ValueError as error:
            st.error(str(error))
    status = budget_status(database.get_budgets(month), database.get_expenses(), month)
    st.subheader(f"Budget status · {month}")
    if status.empty:
        st.info("No budgets have been set for this month.")
    else:
        st.dataframe(status, hide_index=True, width="stretch", column_config={
            "budget_amount": st.column_config.NumberColumn("Budget Amount", format="₹%.2f"),
            "actual_expense": st.column_config.NumberColumn("Actual Expense", format="₹%.2f"),
            "remaining_budget": st.column_config.NumberColumn("Remaining Budget", format="₹%.2f"),
            "utilization": st.column_config.ProgressColumn("Budget Utilization", min_value=0, max_value=100, format="%.1f%%"),
            "exceeded_amount": st.column_config.NumberColumn("Exceeded Amount", format="₹%.2f"),
        })
    budgets = database.get_budgets(month)
    if not budgets.empty:
        choices = {f"{row.category} · ₹{row.budget_amount:,.2f}": int(row.budget_id) for row in budgets.itertuples(index=False)}
        selected = st.selectbox("Remove a budget", list(choices), key="remove_budget")
        if st.button("Delete selected budget"):
            database.delete_budget(choices[selected])
            st.success("Budget removed.")
            st.rerun()
