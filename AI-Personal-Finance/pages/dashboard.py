from datetime import datetime
from html import escape
import logging
import math
import os

import pandas as pd
import plotly.express as px
import streamlit as st

from analysis.spending_analysis import budget_status, category_summary, current_month_expense, financial_alerts, monthly_summary
from database import database
from utils.helpers import finance_summary
from utils.theme import icon_svg


logger = logging.getLogger(__name__)


def _navigate(page: str) -> None:
    st.session_state["main_navigation"] = page


def _low_balance_threshold() -> float:
    raw_value = os.environ.get("FINANCE_LOW_BALANCE_THRESHOLD", "0")
    try:
        threshold = float(raw_value)
    except ValueError:
        logger.warning("Invalid FINANCE_LOW_BALANCE_THRESHOLD value %r; using 0.", raw_value)
        return 0.0
    if not math.isfinite(threshold) or threshold < 0:
        logger.warning("FINANCE_LOW_BALANCE_THRESHOLD must be finite and non-negative; using 0.")
        return 0.0
    return threshold


def _card_header(title: str, note: str, icon_name: str) -> None:
    st.markdown(
        f'<div class="finance-card-head"><div><div class="finance-card-title">{escape(title)}</div>'
        f'<div class="finance-card-note">{escape(note)}</div></div>'
        f'<div class="finance-card-icon">{icon_svg(icon_name, 18)}</div></div>',
        unsafe_allow_html=True,
    )


def _empty_state(title: str, message: str, icon_name: str, button: str, page: str, key: str) -> None:
    st.markdown(
        f'<div class="empty-state"><div class="empty-icon">{icon_svg(icon_name, 20)}</div>'
        f'<div class="empty-title">{escape(title)}</div><div class="empty-copy">{escape(message)}</div></div>',
        unsafe_allow_html=True,
    )
    st.button(button, key=key, icon=":material/add:", on_click=_navigate, args=(page,))


def _metric_card(label: str, value: str, icon_name: str, tone: str, note: str) -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-card-top"><span>{escape(label)}</span>'
        f'<span class="metric-card-icon {tone}">{icon_svg(icon_name, 19)}</span></div>'
        f'<div class="metric-card-value">{escape(value)}</div>'
        f'<div class="metric-card-foot">{note}</div></div>',
        unsafe_allow_html=True,
    )


def _month_change(monthly: pd.DataFrame, column: str) -> str:
    if len(monthly) < 2:
        return "No prior-month baseline yet"
    previous = float(monthly[column].iloc[-2])
    current = float(monthly[column].iloc[-1])
    if previous == 0:
        return "Activity started this month" if current else "No change from prior month"
    percentage = (current - previous) / abs(previous) * 100
    return f"{percentage:+.1f}% vs prior recorded month"


def _style_chart(chart: object) -> object:
    chart.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter, Segoe UI, sans-serif", "color": "#71808c", "size": 11},
        margin={"l": 8, "r": 8, "t": 12, "b": 8},
        legend={"orientation": "h", "y": 1.12, "x": 0},
        xaxis={"showgrid": False, "zeroline": False, "title": None},
        yaxis={"gridcolor": "#edf0f2", "zeroline": False, "title": None, "tickprefix": "₹"},
        hoverlabel={"bgcolor": "#172b3a", "font_color": "#ffffff"},
    )
    return chart


def _budget_progress(category: str, spent: float, budget: float, status: str) -> str:
    utilization = spent / budget * 100 if budget else 0.0
    tone = "danger" if utilization >= 100 else "warning" if utilization >= 85 else ""
    width = min(max(utilization, 0), 100)
    return (
        '<div class="budget-row"><div class="budget-row-top">'
        f'<strong>{escape(category)}</strong><span>₹{spent:,.0f} / ₹{budget:,.0f}</span></div>'
        f'<div class="budget-track"><div class="budget-fill {tone}" style="width:{width:.1f}%"></div></div>'
        f'<div class="budget-row-foot"><span>{utilization:.0f}% used</span><span>{escape(status)}</span></div></div>'
    )


def _insight(icon_name: str, title: str, message: str) -> None:
    st.markdown(
        f'<div class="insight-item"><div class="insight-icon">{icon_svg(icon_name, 16)}</div>'
        f'<div><div class="insight-title">{escape(title)}</div>'
        f'<div class="insight-copy">{escape(message)}</div></div></div>',
        unsafe_allow_html=True,
    )


def render() -> None:
    today = datetime.now().date()
    income = database.get_income()
    expenses = database.get_expenses()
    summary = finance_summary(income, expenses)
    monthly = monthly_summary(income, expenses)
    categories = category_summary(expenses)
    current_month = today.strftime("%Y-%m")
    budgets = database.get_budgets(current_month)
    budget_rows = budget_status(budgets, expenses, current_month)
    alerts = financial_alerts(income, expenses, budgets, current_month,
                              _low_balance_threshold(), as_of=today)
    prediction = database.get_latest_prediction()
    notice = st.session_state.pop("dashboard_notice", None)
    if notice:
        st.success(notice)

    hour = datetime.now().hour
    greeting = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    header, summary_panel, add = st.columns([6, 2.2, 1.7], gap="large")
    with header:
        st.markdown(f'<div class="page-greeting">{greeting}</div>', unsafe_allow_html=True)
        st.title("Personal Finance Dashboard")
        st.markdown('<div class="page-subtitle">Track income, expenses, budgets, and goals in one clear view.</div>', unsafe_allow_html=True)
    with summary_panel:
        st.markdown(
            """
            <div class="summary-pill-wrap">
                <div class="summary-pill">
                    <span class="summary-pill-label">Portfolio health</span>
                    <span class="summary-pill-value">{status}</span>
                </div>
            </div>
            """.format(
                status=("No records" if income.empty and expenses.empty else
                        "Surplus" if summary["savings"] >= 0 else "Deficit")
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="mini-summary"><span>Updated</span><strong>{datetime.now().strftime("%b %d, %Y")}</strong></div>',
            unsafe_allow_html=True,
        )
    with add:
        st.button("Add transaction", type="primary", icon=":material/add:", on_click=_navigate, args=("Transactions",), width="stretch")

    st.write("")
    cards = st.columns(3, gap="medium")
    with cards[0]:
        _metric_card("Total income", f"₹{summary['income']:,.2f}", "income", "green", _month_change(monthly, "income"))
    with cards[1]:
        _metric_card("Total expenses", f"₹{summary['expenses']:,.2f}", "expense", "red", _month_change(monthly, "expenses"))
    with cards[2]:
        balance_tone = "green" if summary["savings"] >= 0 else "red"
        balance_note = (
            f"Savings rate {summary['savings_percentage']:.1f}%; net of recorded activity, not bank cash."
            if summary["income"] else "Net of recorded activity; bank account balances are not tracked."
        )
        _metric_card("Net balance", f"₹{summary['savings']:,.2f}", "wallet", balance_tone, balance_note)

    st.write("")
    left, right = st.columns([1.55, 1], gap="medium")
    with left:
        with st.container(border=True):
            _card_header("Income vs Expenses", "Monthly cash flow from your recorded transactions", "trend")
            if monthly.empty:
                _empty_state("No transaction data yet", "Add your first income or expense to see your financial insights.", "chart", "Add transaction", "Transactions", "empty_chart_add")
            else:
                chart = px.bar(
                    monthly, x="month", y=["income", "expenses"], barmode="group",
                    color_discrete_map={"income": "#4b9a7b", "expenses": "#668bd2"},
                    labels={"month": "Month", "value": "Amount (₹)", "variable": "Type"},
                )
                chart.update_traces(marker_line_width=0, opacity=0.92)
                chart.update_layout(bargap=0.5, bargroupgap=0.15)
                st.plotly_chart(_style_chart(chart), width="stretch", config={"displayModeBar": False, "responsive": True})
    with right:
        with st.container(border=True):
            _card_header("Expense Breakdown", "Where your recorded spending goes", "pie")
            if categories.empty:
                _empty_state("No transaction data yet", "Add an expense to see your category breakdown.", "receipt", "Add transaction", "Transactions", "empty_category_add")
            else:
                chart = px.pie(
                    categories, names="category", values="amount", hole=0.64,
                    color_discrete_sequence=["#3e8a72", "#5d83c4", "#d39a54", "#718695", "#84b4a1", "#bd756b", "#97a6bc", "#accbb9", "#d2b585"],
                    custom_data=[categories["percentage"]],
                )
                chart.update_traces(textposition="inside", texttemplate="%{customdata[0]:.0f}%",
                                    hovertemplate="%{label}<br>₹%{value:,.2f}<br>%{customdata[0]:.1f}%<extra></extra>")
                chart.update_layout(showlegend=True, legend={"orientation": "h", "y": -0.08, "x": 0},
                                    margin={"l": 5, "r": 5, "t": 4, "b": 8})
                st.plotly_chart(_style_chart(chart), width="stretch", config={"displayModeBar": False, "responsive": True})

    st.write("")
    left, right = st.columns([1.4, 1], gap="medium")
    with left:
        with st.container(border=True):
            table_head, table_action = st.columns([5, 1.2])
            with table_head:
                _card_header("Recent Transactions", "Your latest recorded activity", "receipt")
            with table_action:
                st.button("View all", on_click=_navigate, args=("Transactions",), key="view_all_transactions")
            transactions = database.get_transactions().head(7)
            if transactions.empty:
                _empty_state("No transactions yet", "Your recent transactions will appear here.", "receipt", "Add transaction", "Transactions", "empty_transactions_add")
            else:
                display = transactions.copy()
                saved_names = display["name"].fillna("").str.strip()
                descriptions = display["description"].fillna("").str.strip()
                fallback_names = descriptions.where(descriptions.ne(""), display["category_or_source"])
                display["Name"] = saved_names.where(saved_names.ne(""), fallback_names)
                display["Date"] = pd.to_datetime(display["date"], errors="coerce").dt.strftime("%b %d, %Y").fillna("")
                display["Amount"] = display.apply(
                    lambda row: f"{'+' if row['transaction_type'] == 'Income' else '−'}₹{row['amount']:,.2f}", axis=1
                )
                st.dataframe(
                    display[["Name", "category_or_source", "Date", "transaction_type", "Amount"]].rename(
                        columns={"category_or_source": "Category", "transaction_type": "Type"}
                    ),
                    hide_index=True, width="stretch", height=min(48 + len(display) * 42, 340),
                    column_config={"Name": st.column_config.TextColumn(width="large"),
                                   "Category": st.column_config.TextColumn(width="medium"),
                                   "Date": st.column_config.TextColumn(width="small"),
                                   "Type": st.column_config.TextColumn(width="small"),
                                   "Amount": st.column_config.TextColumn(width="medium")},
                )
    with right:
        with st.container(border=True):
            _card_header("Budget Overview", current_month, "calendar")
            st.markdown(
                f'<div class="budget-row-top"><strong>All expenses this month</strong>'
                f'<span>₹{current_month_expense(expenses, current_month):,.2f}</span></div>',
                unsafe_allow_html=True,
            )
            if budget_rows.empty:
                _empty_state("No budget set for this month", "Set category limits to keep monthly spending on track.", "wallet", "Create budget", "Budgets", "empty_budget_add")
            else:
                total_budget = float(budget_rows["budget_amount"].sum())
                total_spent = float(budget_rows["actual_expense"].sum())
                remaining = total_budget - total_spent
                utilization = total_spent / total_budget * 100 if total_budget else 0.0
                tone_class = "danger" if utilization >= 100 else "warning" if utilization >= 85 else ""
                st.markdown(
                    f'<div class="budget-row-top"><strong>Spend in budgeted categories</strong><span>₹{total_spent:,.2f} / ₹{total_budget:,.2f}</span></div>'
                    f'<div class="budget-track"><div class="budget-fill {tone_class}" style="width:{min(max(utilization, 0), 100):.1f}%"></div></div>'
                    f'<div class="budget-row-foot"><span>{utilization:.1f}% used</span><span>₹{remaining:,.2f} remaining</span></div>',
                    unsafe_allow_html=True,
                )
                for row in budget_rows.sort_values("utilization", ascending=False).head(3).itertuples(index=False):
                    st.markdown(_budget_progress(row.category, float(row.actual_expense), float(row.budget_amount), row.status), unsafe_allow_html=True)
                st.button("Manage budgets", on_click=_navigate, args=("Budgets",), key="manage_budgets", width="stretch")

    st.write("")
    left, right = st.columns([1.35, 1], gap="medium")
    with left:
        with st.container(border=True):
            _card_header("Financial Alerts", "Cash flow, balance, budgets, and historical spending", "bell")
            if budgets.empty:
                st.info("Budget-limit alerts are unavailable until you set a monthly category budget.", icon=":material/info:")
            if not alerts:
                if income.empty and expenses.empty:
                    st.info("Record transactions to enable financial alerts.", icon=":material/info:")
                else:
                    st.success("No active financial alerts.", icon=":material/check_circle:")
            else:
                for alert in alerts:
                    if alert["severity"] == "error":
                        st.error(alert["message"], icon=":material/warning:")
                    elif alert["severity"] == "warning":
                        st.warning(alert["message"], icon=":material/warning:")
                    else:
                        st.info(alert["message"], icon=":material/info:")
    with right:
        with st.container(border=True):
            _card_header("AI Financial Insights", "Data-led observations from your account", "sparkles")
            if categories.empty:
                _insight("trend", "Spending trend", "Record expenses across months to reveal how your spending changes.")
                _insight("savings", "Savings opportunity", "Add income and expenses to get a useful, personalized savings observation.")
            else:
                top_category = categories.iloc[0]
                _insight("pie", "Highest spending category", f"{top_category['category']} leads at ₹{top_category['amount']:,.2f} ({top_category['percentage']:.1f}% of recorded expenses).")
                trend = _month_change(monthly, "expenses")
                _insight("trend", "Spending trend", f"Your latest recorded monthly expense change: {trend}.")
                if summary["savings"] < 0:
                    suggestion = "Recorded expenses exceed income. Review flexible categories and upcoming bills."
                else:
                    suggestion = f"Reviewing {top_category['category']} spending is one place to look for possible savings."
                _insight("savings", "Savings suggestion", suggestion)
            if prediction:
                _insight("calendar", "Next month estimate", f"₹{prediction['predicted_amount']:,.2f} for {prediction['prediction_month']} using {prediction['model_name']}.")
            else:
                _insight("calendar", "Next month estimate", "Train and run a forecast from Predictions when enough expense history is available.")
            st.button("Open AI assistant", on_click=_navigate, args=("AI Assistant",), key="open_ai_assistant")
