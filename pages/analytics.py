import plotly.express as px
import streamlit as st

from analysis.spending_analysis import category_summary, monthly_summary
from database import database


def render() -> None:
    st.title("Spending Analytics")
    income, expenses = database.get_income(), database.get_expenses()
    categories = category_summary(expenses)
    monthly = monthly_summary(income, expenses)
    total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
    avg_month = float(monthly["expenses"].mean()) if not monthly.empty else 0.0
    highest = categories.iloc[0]["category"] if not categories.empty else "Not available"
    lowest = categories.iloc[-1]["category"] if not categories.empty else "Not available"
    first, second, third, fourth = st.columns(4)
    first.metric("Total spending", f"₹{total:,.2f}")
    second.metric("Average monthly spending", f"₹{avg_month:,.2f}")
    third.metric("Highest spending category", highest)
    fourth.metric("Lowest spending category", lowest)
    if expenses.empty:
        st.info("Add expense history to see detailed analytics.")
        return
    left, right = st.columns(2)
    with left:
        st.plotly_chart(px.bar(categories, x="category", y="amount", title="Spending by Category", color="category"), use_container_width=True)
        st.plotly_chart(px.line(monthly, x="month", y="expenses", markers=True, title="Monthly Spending"), use_container_width=True)
    with right:
        st.plotly_chart(px.pie(categories, names="category", values="percentage", hole=0.5, title="Category Percentages"), use_container_width=True)
        st.plotly_chart(px.area(monthly, x="month", y="savings", title="Savings Trend"), use_container_width=True)
    st.subheader("Monthly details")
    st.dataframe(monthly, hide_index=True, use_container_width=True)
    if len(monthly) > 1:
        last_growth = monthly["expense_growth"].iloc[-1]
        if last_growth == last_growth:
            st.caption(f"Latest monthly expense growth: {last_growth:.1f}%")
