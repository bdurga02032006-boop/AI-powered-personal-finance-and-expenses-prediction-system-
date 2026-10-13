from datetime import date

import streamlit as st

from database import database
from utils.helpers import CATEGORIES, PAYMENT_METHODS, validate_amount, validate_date, validate_text


def render() -> None:
    st.title("Transactions")
    income_tab, expense_tab, manage_tab = st.tabs(["Add income", "Add expense", "Manage transactions"])
    with income_tab:
        with st.form("add_income", clear_on_submit=True):
            income_date = st.date_input("Date", value=date.today(), key="income_date")
            amount = st.number_input("Amount (₹)", min_value=0.01, step=100.0, format="%.2f", key="income_amount")
            source = st.text_input("Source", max_chars=120, key="income_source")
            description = st.text_input("Description", max_chars=250, key="income_description")
            submitted = st.form_submit_button("Add income", type="primary")
        if submitted:
            try:
                database.add_income(validate_date(income_date), validate_amount(amount), validate_text(source, "Source"), description.strip()[:250])
                st.success("Income added.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    with expense_tab:
        with st.form("add_expense", clear_on_submit=True):
            expense_date = st.date_input("Date", value=date.today(), key="expense_date")
            category = st.selectbox("Category", CATEGORIES)
            amount = st.number_input("Amount (₹)", min_value=0.01, step=50.0, format="%.2f", key="expense_amount")
            payment_method = st.selectbox("Payment method", PAYMENT_METHODS)
            description = st.text_input("Description", max_chars=250, key="expense_description")
            submitted = st.form_submit_button("Add expense", type="primary")
        if submitted:
            try:
                database.add_expense(validate_date(expense_date), category, validate_amount(amount), payment_method, description.strip()[:250])
                st.success("Expense added.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
    with manage_tab:
        transactions = database.get_transactions()
        if transactions.empty:
            st.info("There are no transactions to manage yet.")
        else:
            st.dataframe(transactions, hide_index=True, use_container_width=True)
            options = {
                f"{row.transaction_type} #{row.transaction_id} · {row.date} · ₹{row.amount:,.2f}": row
                for row in transactions.itertuples(index=False)
            }
            selected_label = st.selectbox("Select a transaction", list(options))
            selected = options[selected_label]
            is_expense = selected.transaction_type == "Expense"
            with st.form("edit_transaction"):
                selected_date = st.date_input("Date", value=date.fromisoformat(str(selected.date)[:10]), key="edit_date")
                selected_amount = st.number_input("Amount (₹)", min_value=0.01, value=float(selected.amount), step=50.0, format="%.2f", key="edit_amount")
                if is_expense:
                    default_category = selected.category_or_source if selected.category_or_source in CATEGORIES else CATEGORIES[0]
                    selected_category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(default_category), key="edit_category")
                    default_payment = selected.payment_method if selected.payment_method in PAYMENT_METHODS else PAYMENT_METHODS[0]
                    selected_payment = st.selectbox("Payment method", PAYMENT_METHODS, index=PAYMENT_METHODS.index(default_payment), key="edit_payment")
                else:
                    selected_category = st.text_input("Source", value=selected.category_or_source, max_chars=120, key="edit_source")
                    selected_payment = ""
                selected_description = st.text_input("Description", value=selected.description or "", max_chars=250, key="edit_description")
                update = st.form_submit_button("Save changes")
            if update:
                try:
                    database.update_transaction(
                        selected.transaction_type, int(selected.transaction_id), validate_date(selected_date),
                        validate_amount(selected_amount), validate_text(selected_category, "Category or source"),
                        selected_payment, selected_description.strip()[:250],
                    )
                    st.success("Transaction updated.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
            if st.button("Delete selected transaction", type="secondary"):
                try:
                    database.delete_transaction(selected.transaction_type, int(selected.transaction_id))
                    st.success("Transaction deleted.")
                    st.rerun()
                except ValueError as error:
                    st.error(str(error))
