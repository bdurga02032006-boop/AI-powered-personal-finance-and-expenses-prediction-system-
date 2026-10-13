import streamlit as st

from database.database import DB_PATH, initialize_database
from pages import ai_assistant, analytics, budget, dashboard, goals, predictions, reports, transactions
from utils.theme import apply_theme, icon_svg


st.set_page_config(page_title="Personal Finance", page_icon="₹", layout="wide")
initialize_database()
apply_theme()

with st.sidebar:
    st.markdown(
        f'<div class="finance-brand"><div class="finance-brand-mark">{icon_svg("wallet", 21)}</div>'
        '<div><div class="finance-brand-name">Personal Finance</div>'
        '<div class="finance-brand-sub">Your money, in focus</div></div></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="sidebar-section-label">Workspace</div>', unsafe_allow_html=True)
    nav_options = ["Dashboard", "Transactions", "Budgets", "Goals", "Reports", "Predictions", "AI Assistant"]
    nav_icons = {
        "Dashboard": "space_dashboard",
        "Transactions": "receipt_long",
        "Budgets": "savings",
        "Goals": "flag",
        "Reports": "monitoring",
        "Predictions": "query_stats",
        "AI Assistant": "auto_awesome",
    }
    page = st.radio(
        "Navigation",
        nav_options,
        format_func=lambda item: f":material/{nav_icons[item]}: {item}",
        index=0,
        key="main_navigation",
        label_visibility="visible",
        horizontal=False,
    )
    with st.popover("Settings", icon=":material/settings:", width="stretch"):
        st.caption("Local workspace settings")
        st.write(f"Database file: `{DB_PATH.name}`")
        st.write("AI service: Ollama on this device")
    st.markdown(
        '<div class="sidebar-profile"><div class="sidebar-avatar">₹</div>'
        '<div><div class="sidebar-user">Local workspace</div>'
        '<div class="sidebar-account">SQLite · this device</div></div></div>',
        unsafe_allow_html=True,
    )

{
    "Dashboard": dashboard.render,
    "Transactions": transactions.render,
    "Budgets": budget.render,
    "Goals": goals.render,
    "Reports": reports.render,
    "Predictions": predictions.render,
    "AI Assistant": ai_assistant.render,
}[page]()
