from datetime import date

import streamlit as st

from database import database
from utils.helpers import CATEGORIES, PAYMENT_METHODS, validate_amount, validate_date, validate_text


def _persist_income_draft() -> None:
    st.session_state["income_draft"] = {
        "date": st.session_state.get("income_date", date.today()),
        "amount": st.session_state.get("income_amount", 0.01),
        "source": st.session_state.get("income_source", ""),
        "name": st.session_state.get("income_name", ""),
        "description": st.session_state.get("income_description", ""),
    }


def _submit_income() -> None:
    _persist_income_draft()
    try:
        amount = validate_amount(st.session_state["income_amount"])
        description = st.session_state["income_description"].strip()
        if len(description) > 250:
            raise ValueError("Description must be 250 characters or fewer.")
        database.add_income(
            validate_date(st.session_state["income_date"]),
            amount,
            validate_text(st.session_state["income_source"], "Source"),
            description,
            validate_text(st.session_state["income_name"], "Name"),
        )
        _invalidate_predictions()
        income_total = float(database.get_income()["amount"].sum())
        st.session_state["dashboard_notice"] = (
            f"₹{amount:,.2f} added. Total recorded income is now ₹{income_total:,.2f}."
        )
        st.session_state["main_navigation"] = "Dashboard"
    except ValueError as error:
        st.session_state["transaction_error"] = str(error)


def _persist_expense_draft() -> None:
    st.session_state["expense_draft"] = {
        "date": st.session_state.get("expense_date", date.today()),
        "category": st.session_state.get("expense_category", CATEGORIES[0]),
        "amount": st.session_state.get("expense_amount", 0.01),
        "payment": st.session_state.get("expense_payment", PAYMENT_METHODS[0]),
        "name": st.session_state.get("expense_name", ""),
        "description": st.session_state.get("expense_description", ""),
    }


def _invalidate_predictions() -> None:
    st.session_state.pop("training_result", None)
    st.session_state.pop("latest_forecast", None)


def _submit_expense() -> None:
    _persist_expense_draft()
    try:
        database.add_expense(
            validate_date(st.session_state["expense_date"]),
            st.session_state["expense_category"],
            validate_amount(st.session_state["expense_amount"]),
            st.session_state["expense_payment"],
            st.session_state["expense_description"].strip()[:250],
            validate_text(st.session_state["expense_name"], "Name"),
        )
        _invalidate_predictions()
        st.session_state["transaction_notice"] = "Expense saved and shown in recent transactions."
    except ValueError as error:
        st.session_state["transaction_error"] = str(error)


def _show_recent_transactions() -> None:
    recent = database.get_transactions().head(5)
    st.subheader("Recent saved transactions")
    if recent.empty:
        st.caption("Saved income and expenses will appear here.")
        return

    recent = recent.rename(
        columns={
            "transaction_type": "Type",
            "date": "Date",
            "name": "Name",
            "category_or_source": "Category / Source",
            "amount": "Amount",
            "description": "Description",
        }
    )
    st.dataframe(
        recent[["Date", "Type", "Name", "Category / Source", "Amount", "Description"]],
        hide_index=True,
        width="stretch",
        column_config={"Amount": st.column_config.NumberColumn(format="₹%.2f")},
    )


def render() -> None:
    st.title("Transactions")
    notice = st.session_state.pop("transaction_notice", None)
    if notice:
        st.success(notice)
    error = st.session_state.pop("transaction_error", None)
    if error:
        st.error(error)
    _show_recent_transactions()

    income_tab, expense_tab, manage_tab = st.tabs(["Add income", "Add expense", "Manage transactions"])
    with income_tab:
        income_draft = st.session_state.get("income_draft", {})
        st.session_state.setdefault("income_date", income_draft.get("date", date.today()))
        st.session_state.setdefault("income_amount", income_draft.get("amount", 0.01))
        st.session_state.setdefault("income_source", income_draft.get("source", ""))
        st.session_state.setdefault("income_name", income_draft.get("name", ""))
        st.session_state.setdefault("income_description", income_draft.get("description", ""))
        st.number_input(
            "Amount (₹)", min_value=0.01, step=100.0, format="%.2f",
            key="income_amount", on_change=_persist_income_draft,
            help="Enter a positive income amount in rupees.", label_visibility="visible",
        )
        st.date_input("Date", key="income_date", on_change=_persist_income_draft, label_visibility="visible")
        st.text_input(
            "Source", max_chars=120, key="income_source", on_change=_persist_income_draft,
            placeholder="e.g., Salary or freelance work", label_visibility="visible",
        )
        st.text_input(
            "Name", max_chars=120, key="income_name", on_change=_persist_income_draft,
            placeholder="e.g., October salary", label_visibility="visible",
        )
        st.text_input(
            "Description", max_chars=250, key="income_description", on_change=_persist_income_draft,
            placeholder="Optional note about this income", label_visibility="visible",
        )
        st.button("Add income", type="primary", key="submit_income", on_click=_submit_income)
    with expense_tab:
        expense_draft = st.session_state.get("expense_draft", {})
        st.session_state.setdefault("expense_date", expense_draft.get("date", date.today()))
        st.session_state.setdefault("expense_category", expense_draft.get("category", CATEGORIES[0]))
        st.session_state.setdefault("expense_amount", expense_draft.get("amount", 0.01))
        st.session_state.setdefault("expense_payment", expense_draft.get("payment", PAYMENT_METHODS[0]))
        st.session_state.setdefault("expense_name", expense_draft.get("name", ""))
        st.session_state.setdefault("expense_description", expense_draft.get("description", ""))
        st.date_input("Date", key="expense_date", on_change=_persist_expense_draft)
        st.selectbox("Category", CATEGORIES, key="expense_category", on_change=_persist_expense_draft)
        st.number_input(
            "Amount (₹)", min_value=0.01, step=50.0, format="%.2f",
            key="expense_amount", on_change=_persist_expense_draft,
        )
        st.selectbox("Payment method", PAYMENT_METHODS, key="expense_payment", on_change=_persist_expense_draft)
        st.text_input("Name", max_chars=120, key="expense_name", on_change=_persist_expense_draft)
        st.text_input("Description", max_chars=250, key="expense_description", on_change=_persist_expense_draft)
        st.button("Add expense", type="primary", key="submit_expense", on_click=_submit_expense)
    with manage_tab:
        transactions = database.get_transactions()
        if transactions.empty:
            st.info("There are no transactions to manage yet.")
            return
        st.dataframe(transactions, hide_index=True, width="stretch")
        options = {f"{r.transaction_type} #{r.transaction_id} · {r.date} · ₹{r.amount:,.2f}": r for r in transactions.itertuples(index=False)}
        selected = options[st.selectbox("Select a transaction", list(options))]
        expense = selected.transaction_type == "Expense"
        with st.form("edit_transaction"):
            selected_date = st.date_input("Date", value=date.fromisoformat(str(selected.date)[:10]), key="edit_date")
            selected_amount = st.number_input("Amount (₹)", min_value=0.01, value=float(selected.amount), step=50.0, format="%.2f", key="edit_amount")
            selected_name = st.text_input("Name", value=selected.name or "", max_chars=120, key="edit_name")
            if expense:
                category = selected.category_or_source if selected.category_or_source in CATEGORIES else CATEGORIES[0]
                category_or_source = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(category), key="edit_category")
                payment = selected.payment_method if selected.payment_method in PAYMENT_METHODS else PAYMENT_METHODS[0]
                selected_payment = st.selectbox("Payment method", PAYMENT_METHODS, index=PAYMENT_METHODS.index(payment), key="edit_payment")
            else:
                category_or_source = st.text_input("Source", value=selected.category_or_source, max_chars=120, key="edit_source")
                selected_payment = ""
            description = st.text_input("Description", value=selected.description or "", max_chars=250, key="edit_description")
            update = st.form_submit_button("Save changes")
        if update:
            try:
                database.update_transaction(selected.transaction_type, int(selected.transaction_id), validate_date(selected_date),
                                           validate_amount(selected_amount), validate_text(category_or_source, "Category or source"),
                                           selected_payment, description.strip()[:250], validate_text(selected_name, "Name"))
                _invalidate_predictions()
                st.session_state["transaction_notice"] = "Transaction updated."
                st.rerun()
            except ValueError as error:
                st.error(str(error))
        if st.button("Delete selected transaction"):
            try:
                database.delete_transaction(selected.transaction_type, int(selected.transaction_id))
                _invalidate_predictions()
                st.session_state["transaction_notice"] = "Transaction deleted."
                st.rerun()
            except ValueError as error:
                st.error(str(error))
