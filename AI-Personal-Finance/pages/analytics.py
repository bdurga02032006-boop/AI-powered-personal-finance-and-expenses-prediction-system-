import plotly.express as px
import streamlit as st

from analysis.spending_analysis import category_summary, monthly_summary
from database import database


def render() -> None:
    st.title("Spending Analytics")
    st.caption("Explore category spending, monthly cash flow, and savings from your recorded transactions.")
    income, expenses = database.get_income(), database.get_expenses()
    categories = category_summary(expenses)
    monthly = monthly_summary(income, expenses)
    total = float(expenses["amount"].sum()) if not expenses.empty else 0.0
    average = float(monthly["expenses"].mean()) if not monthly.empty else 0.0
    highest = categories.iloc[0]["category"] if not categories.empty else "Not available"
    lowest = categories.iloc[-1]["category"] if not categories.empty else "Not available"
    columns = st.columns(4)
    columns[0].metric("Total spending", f"₹{total:,.2f}")
    columns[1].metric("Average monthly spending", f"₹{average:,.2f}")
    columns[2].metric("Highest spending category", highest)
    columns[3].metric("Lowest spending category", lowest)
    if expenses.empty:
        st.info("Add expense history to see detailed analytics.")
        return
    left, right = st.columns([1.1, 0.9], gap="large")
    with left:
        with st.container(border=True):
            category_chart = px.bar(
                categories, x="category", y="amount", title="Spending by category",
                color_discrete_sequence=["#237a5c"],
            )
            category_chart.update_traces(marker_line_width=0, opacity=0.9)
            category_chart.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#718078", "size": 11},
                margin={"l": 8, "r": 8, "t": 42, "b": 8},
                xaxis={"showgrid": False, "zeroline": False, "title": None},
                yaxis={"gridcolor": "#edf0f2", "zeroline": False, "title": None},
            )
            st.plotly_chart(category_chart, width="stretch", config={"displayModeBar": False, "responsive": True})
        with st.container(border=True):
            spending_chart = px.line(monthly, x="month", y="expenses", markers=True, title="Monthly spending")
            spending_chart.update_traces(line={"color": "#237a5c", "width": 3}, marker={"size": 7})
            spending_chart.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#718078", "size": 11},
                margin={"l": 8, "r": 8, "t": 42, "b": 8},
                xaxis={"showgrid": False, "zeroline": False, "title": None},
                yaxis={"gridcolor": "#edf0f2", "zeroline": False, "title": None},
            )
            st.plotly_chart(spending_chart, width="stretch", config={"displayModeBar": False, "responsive": True})
    with right:
        with st.container(border=True):
            category_share_chart = px.pie(
                categories, names="category", values="percentage", hole=0.62, title="Category share",
                color_discrete_sequence=["#237a5c", "#4e7890", "#d2a15e", "#81928a", "#91b49d", "#bf756a", "#97a6bc", "#accbb9", "#d2b585"],
            )
            category_share_chart.update_traces(
                textposition="inside", texttemplate="%{percent:.0%}",
                hovertemplate="%{label}<br>%{value:.1f}%<extra></extra>",
            )
            category_share_chart.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#718078", "size": 11},
                margin={"l": 8, "r": 8, "t": 42, "b": 8},
                legend={"orientation": "h", "y": -0.08, "x": 0},
            )
            st.plotly_chart(category_share_chart, width="stretch", config={"displayModeBar": False, "responsive": True})
        with st.container(border=True):
            savings_chart = px.area(monthly, x="month", y="savings", title="Savings trend")
            savings_chart.update_traces(line={"color": "#4e7890", "width": 2.5}, fillcolor="rgba(78,120,144,.16)")
            savings_chart.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                font={"family": "Inter, Segoe UI, sans-serif", "color": "#718078", "size": 11},
                margin={"l": 8, "r": 8, "t": 42, "b": 8},
                xaxis={"showgrid": False, "zeroline": False, "title": None},
                yaxis={"gridcolor": "#edf0f2", "zeroline": False, "title": None},
            )
            st.plotly_chart(savings_chart, width="stretch", config={"displayModeBar": False, "responsive": True})
    st.subheader("Monthly details")
    st.dataframe(monthly, hide_index=True, width="stretch", column_config={
        "income": st.column_config.NumberColumn("Income", format="₹%.2f"),
        "expenses": st.column_config.NumberColumn("Expenses", format="₹%.2f"),
        "savings": st.column_config.NumberColumn("Net savings", format="₹%.2f"),
        "expense_growth": st.column_config.NumberColumn("Expense growth", format="%.1f%%"),
    })
    if len(monthly) > 1 and pd_not_null(monthly["expense_growth"].iloc[-1]):
        st.caption(f"Latest monthly expense growth: {monthly['expense_growth'].iloc[-1]:.1f}%")


def pd_not_null(value: object) -> bool:
    return value is not None and value == value
