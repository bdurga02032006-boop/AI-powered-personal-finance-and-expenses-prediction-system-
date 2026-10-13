"""SQLite persistence and parameterized finance-data operations."""

from contextlib import contextmanager
from pathlib import Path
import sqlite3
from typing import Any, Iterator

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "finance.db"
DEFAULT_USER_ID = 1


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database() -> None:
    schema = (PROJECT_ROOT / "database" / "schema.sql").read_text(encoding="utf-8")
    with get_connection() as connection:
        connection.executescript(schema)
        for table in ("income", "expenses"):
            columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
            if "name" not in columns:
                connection.execute(f"ALTER TABLE {table} ADD COLUMN name TEXT NOT NULL DEFAULT ''")
        connection.execute(
            "INSERT OR IGNORE INTO users (user_id, name, email) VALUES (?, ?, ?)",
            (DEFAULT_USER_ID, "Local User", "local-user@localhost"),
        )


def _dataframe(query: str, parameters: tuple[Any, ...] = ()) -> pd.DataFrame:
    with get_connection() as connection:
        return pd.read_sql_query(query, connection, params=parameters)


def get_income() -> pd.DataFrame:
    return _dataframe(
        "SELECT income_id, user_id, income_date, amount, source, description, name "
        "FROM income WHERE user_id = ? ORDER BY income_date, income_id",
        (DEFAULT_USER_ID,),
    )


def get_expenses() -> pd.DataFrame:
    return _dataframe(
        "SELECT expense_id, user_id, expense_date, category, amount, payment_method, description, name "
        "FROM expenses WHERE user_id = ? ORDER BY expense_date, expense_id",
        (DEFAULT_USER_ID,),
    )


def get_transactions() -> pd.DataFrame:
    income = _dataframe(
        "SELECT income_id AS transaction_id, 'Income' AS transaction_type, income_date AS date, "
        "source AS category_or_source, amount, '' AS payment_method, description, name "
        "FROM income WHERE user_id = ?",
        (DEFAULT_USER_ID,),
    )
    expenses = _dataframe(
        "SELECT expense_id AS transaction_id, 'Expense' AS transaction_type, expense_date AS date, "
        "category AS category_or_source, amount, payment_method, description, name "
        "FROM expenses WHERE user_id = ?",
        (DEFAULT_USER_ID,),
    )
    frames = [frame for frame in (income, expenses) if not frame.empty]
    if not frames:
        return pd.DataFrame(columns=["transaction_id", "transaction_type", "date", "category_or_source", "amount", "payment_method", "description", "name"])
    return pd.concat(frames, ignore_index=True).sort_values("date", ascending=False, kind="stable")


def add_income(income_date: str, amount: float, source: str, description: str = "", name: str = "") -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO income (user_id, income_date, amount, source, description, name) VALUES (?, ?, ?, ?, ?, ?)",
            (DEFAULT_USER_ID, income_date, amount, source, description, name),
        )
        return int(cursor.lastrowid)


def add_expense(expense_date: str, category: str, amount: float, payment_method: str, description: str = "", name: str = "") -> int:
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO expenses (user_id, expense_date, category, amount, payment_method, description, name) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (DEFAULT_USER_ID, expense_date, category, amount, payment_method, description, name),
        )
        return int(cursor.lastrowid)


def update_transaction(
    transaction_type: str,
    transaction_id: int,
    transaction_date: str,
    amount: float,
    category_or_source: str,
    payment_method: str,
    description: str,
    name: str = "",
) -> None:
    if transaction_type == "Income":
        query = "UPDATE income SET income_date = ?, amount = ?, source = ?, description = ?, name = ? WHERE income_id = ? AND user_id = ?"
        parameters = (transaction_date, amount, category_or_source, description, name, transaction_id, DEFAULT_USER_ID)
    elif transaction_type == "Expense":
        query = "UPDATE expenses SET expense_date = ?, amount = ?, category = ?, payment_method = ?, description = ?, name = ? WHERE expense_id = ? AND user_id = ?"
        parameters = (transaction_date, amount, category_or_source, payment_method, description, name, transaction_id, DEFAULT_USER_ID)
    else:
        raise ValueError("Transaction type must be Income or Expense.")
    with get_connection() as connection:
        cursor = connection.execute(query, parameters)
        if cursor.rowcount != 1:
            raise ValueError("Transaction was not found.")


def delete_transaction(transaction_type: str, transaction_id: int) -> None:
    table, id_column = {"Income": ("income", "income_id"), "Expense": ("expenses", "expense_id")}.get(
        transaction_type, (None, None)
    )
    if table is None:
        raise ValueError("Transaction type must be Income or Expense.")
    with get_connection() as connection:
        cursor = connection.execute(
            f"DELETE FROM {table} WHERE {id_column} = ? AND user_id = ?",
            (transaction_id, DEFAULT_USER_ID),
        )
        if cursor.rowcount != 1:
            raise ValueError("Transaction was not found.")


def get_budgets(month: str | None = None) -> pd.DataFrame:
    query = "SELECT budget_id, category, month, budget_amount FROM budgets WHERE user_id = ?"
    parameters: tuple[Any, ...] = (DEFAULT_USER_ID,)
    if month is not None:
        query += " AND month = ?"
        parameters += (month,)
    return _dataframe(query + " ORDER BY month DESC, category", parameters)


def save_budget(category: str, month: str, amount: float) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO budgets (user_id, category, month, budget_amount) VALUES (?, ?, ?, ?) "
            "ON CONFLICT(user_id, category, month) DO UPDATE SET budget_amount = excluded.budget_amount",
            (DEFAULT_USER_ID, category, month, amount),
        )


def delete_budget(budget_id: int) -> None:
    with get_connection() as connection:
        connection.execute("DELETE FROM budgets WHERE budget_id = ? AND user_id = ?", (budget_id, DEFAULT_USER_ID))


def save_prediction(month: str, amount: float, model_name: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "INSERT INTO predictions (user_id, prediction_month, predicted_amount, model_name) VALUES (?, ?, ?, ?)",
            (DEFAULT_USER_ID, month, amount, model_name),
        )


def get_latest_prediction() -> dict[str, Any] | None:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT prediction_month, predicted_amount, model_name, created_at FROM predictions "
            "WHERE user_id = ? ORDER BY prediction_id DESC LIMIT 1",
            (DEFAULT_USER_ID,),
        ).fetchone()
    return dict(row) if row else None
