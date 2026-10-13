"""Fast local smoke tests for persistence, analysis, ML, and Ollama fallback."""

from datetime import date
from pathlib import Path
import tempfile
import unittest
import sqlite3
from unittest.mock import patch

import pandas as pd
import requests
from streamlit.testing.v1 import AppTest

from ai.financial_assistant import LOCAL_ONLY_MESSAGE, OLLAMA_UNAVAILABLE, generate_financial_response
from analysis.spending_analysis import budget_status, financial_alerts, monthly_summary
from database import database
from models import expense_model
from models.expense_model import ArtifactLoadError
from models.train_model import train_and_compare
from prediction.expense_predictor import predict_next_month
from utils.helpers import finance_summary, validate_amount
from utils.preprocessing import build_feature_frame


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FinanceSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temp.name) / "finance.db"
        database.initialize_database()

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        self.temp.cleanup()

    def test_schema_and_transaction_crud(self) -> None:
        with database.get_connection() as connection:
            names = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertTrue({"users", "income", "expenses", "budgets", "predictions"}.issubset(names))
        income_id = database.add_income("2026-10-01", 50000, "Salary", "Monthly", "October salary")
        expense_id = database.add_expense("2026-10-02", "Food", 900, "UPI", "Groceries", "Weekly shop")
        self.assertEqual(len(database.get_transactions()), 2)
        database.update_transaction("Income", income_id, "2026-10-01", 52000, "Salary", "", "Monthly", "October pay")
        self.assertEqual(float(database.get_income().iloc[0]["amount"]), 52000)
        self.assertEqual(database.get_income().iloc[0]["name"], "October pay")
        database.update_transaction("Expense", expense_id, "2026-10-03", 950, "Food", "UPI", "Groceries", "Weekly shop")
        self.assertEqual(float(database.get_expenses().iloc[0]["amount"]), 950)
        self.assertEqual(database.get_expenses().iloc[0]["name"], "Weekly shop")
        database.delete_transaction("Income", income_id)
        database.delete_transaction("Expense", expense_id)
        self.assertTrue(database.get_income().empty)
        self.assertTrue(database.get_expenses().empty)

    def test_existing_database_migrates_transaction_names_without_data_loss(self) -> None:
        legacy_path = Path(self.temp.name) / "legacy.db"
        with sqlite3.connect(legacy_path) as connection:
            connection.executescript(
                "CREATE TABLE users (user_id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, created_at TEXT DEFAULT CURRENT_TIMESTAMP);"
                "CREATE TABLE income (income_id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, income_date TEXT NOT NULL, amount REAL NOT NULL, source TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);"
                "CREATE TABLE expenses (expense_id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL, expense_date TEXT NOT NULL, category TEXT NOT NULL, amount REAL NOT NULL, payment_method TEXT NOT NULL, description TEXT NOT NULL DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);"
                "INSERT INTO users (user_id,name,email) VALUES (1,'Local User','local-user@localhost');"
                "INSERT INTO income (user_id,income_date,amount,source) VALUES (1,'2026-10-01',50000,'Salary');"
                "INSERT INTO expenses (user_id,expense_date,category,amount,payment_method) VALUES (1,'2026-10-02','Food',1200,'UPI');"
            )
        original_path = database.DB_PATH
        database.DB_PATH = legacy_path
        try:
            database.initialize_database()
            income = database.get_income().iloc[0]
            expense = database.get_expenses().iloc[0]
            self.assertEqual((float(income["amount"]), income["name"]), (50000.0, ""))
            self.assertEqual((float(expense["amount"]), expense["name"]), (1200.0, ""))
        finally:
            database.DB_PATH = original_path

    def test_transaction_input_drafts_survive_navigation_and_save(self) -> None:
        app = AppTest.from_file(str(PROJECT_ROOT / "app.py")).run()
        app.radio[0].set_value("Transactions").run()
        self.assertEqual(app.number_input(key="income_amount").label, "Amount (₹)")
        self.assertEqual(app.date_input(key="income_date").label, "Date")
        self.assertEqual(app.text_input(key="income_source").label, "Source")
        self.assertEqual(app.text_input(key="income_description").label, "Description")
        app.number_input(key="income_amount").set_value(5000).run()
        app.text_input(key="income_source").set_value("Salary").run()
        app.text_input(key="income_name").set_value("October salary").run()
        app.text_input(key="income_description").set_value("Monthly pay").run()
        app.radio[0].set_value("Dashboard").run()
        app.radio[0].set_value("Transactions").run()
        self.assertEqual(app.number_input(key="income_amount").value, 5000)
        self.assertEqual(app.text_input(key="income_source").value, "Salary")
        self.assertEqual(app.text_input(key="income_name").value, "October salary")
        app.text_input(key="income_source").set_value("").run()
        app.button(key="submit_income").click().run()
        self.assertTrue(any("Source is required" in item.value for item in app.error))
        self.assertTrue(database.get_income().empty)
        app.text_input(key="income_source").set_value("Salary").run()
        app.button(key="submit_income").click().run()
        self.assertFalse(app.exception, [item.message for item in app.exception])
        self.assertEqual(app.radio[0].value, "Dashboard")
        self.assertEqual(float(database.get_income().iloc[0]["amount"]), 5000)
        self.assertEqual(database.get_income().iloc[0]["name"], "October salary")
        self.assertEqual(database.get_income().iloc[0]["description"], "Monthly pay")

        app.radio[0].set_value("Transactions").run()
        app.number_input(key="expense_amount").set_value(1250).run()
        app.selectbox(key="expense_category").set_value("Food").run()
        app.selectbox(key="expense_payment").set_value("UPI").run()
        app.text_input(key="expense_name").set_value("Weekly groceries").run()
        app.text_input(key="expense_description").set_value("Groceries").run()
        app.radio[0].set_value("Dashboard").run()
        app.radio[0].set_value("Transactions").run()
        self.assertEqual(app.number_input(key="expense_amount").value, 1250)
        self.assertEqual(app.text_input(key="expense_description").value, "Groceries")
        self.assertEqual(app.text_input(key="expense_name").value, "Weekly groceries")
        app.button(key="submit_expense").click().run()
        self.assertFalse(app.exception, [item.message for item in app.exception])
        self.assertEqual(float(database.get_expenses().iloc[0]["amount"]), 1250)
        self.assertEqual(database.get_expenses().iloc[0]["name"], "Weekly groceries")

    def test_summary_and_budget_status(self) -> None:
        database.add_income("2026-10-01", 10000, "Salary")
        database.add_expense("2026-10-02", "Food", 900, "UPI")
        self.assertEqual(finance_summary(database.get_income(), database.get_expenses())["savings"], 9100)
        database.save_budget("Food", "2026-10", 1000)
        database.save_budget("Food", "2026-10", 1100)
        status = budget_status(database.get_budgets("2026-10"), database.get_expenses(), "2026-10")
        self.assertEqual(len(status), 1)
        self.assertEqual(status.iloc[0]["status"], "Approaching Limit")

    def test_financial_alerts_use_actual_values_and_require_history(self) -> None:
        database.add_income("2026-10-01", 1000, "Salary")
        database.add_expense("2026-10-02", "Food", 1200, "UPI")
        database.save_budget("Food", "2026-10", 1000)
        alerts = financial_alerts(
            database.get_income(), database.get_expenses(), database.get_budgets("2026-10"),
            "2026-10", low_balance_threshold=500, as_of=date(2026, 10, 15),
        )
        messages = " ".join(alert["message"] for alert in alerts)
        self.assertIn("expenses exceed recorded income by ₹200.00", messages)
        self.assertIn("Food is over budget by ₹200.00", messages)
        self.assertIn("below your ₹500.00 alert threshold", messages)
        self.assertIn("not enough history yet", messages)

        for month in range(3, 9):
            database.add_expense(f"2026-{month:02d}-10", "Food", 100, "UPI")
        database.add_expense("2026-09-10", "Food", 500, "UPI")
        alerts = financial_alerts(
            database.get_income(), database.get_expenses(), database.get_budgets("2026-10"),
            "2026-10", as_of=date(2026, 10, 15),
        )
        self.assertTrue(any("unusually high" in alert["message"] for alert in alerts))

    def test_financial_alerts_validate_threshold_and_empty_data(self) -> None:
        empty = pd.DataFrame()
        self.assertEqual(financial_alerts(empty, empty, empty, "2026-10"), [])
        with self.assertRaises(ValueError):
            financial_alerts(empty, empty, empty, "2026-10", low_balance_threshold=float("nan"))
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_amount(value)

    def test_monthly_summary_with_only_one_transaction_type(self) -> None:
        income = pd.DataFrame({"income_date": ["2026-10-01"], "amount": [1200]})
        expenses = pd.DataFrame({"expense_date": ["2026-10-02"], "amount": [300]})
        empty_income = pd.DataFrame(columns=["income_date", "amount"])
        empty_expenses = pd.DataFrame(columns=["expense_date", "amount"])

        income_only = monthly_summary(income, empty_expenses).iloc[0]
        expense_only = monthly_summary(empty_income, expenses).iloc[0]
        self.assertEqual((income_only["income"], income_only["expenses"], income_only["savings"]), (1200, 0, 1200))
        self.assertEqual((expense_only["income"], expense_only["expenses"], expense_only["savings"]), (0, 300, -300))

    def test_time_aware_model_training_and_artifact(self) -> None:
        sample = pd.read_csv(PROJECT_ROOT / "data" / "sample_expenses.csv")
        income = pd.DataFrame({"income_date": [f"2025-{month:02d}-01" for month in range(1, 13)], "amount": [45000] * 12})
        features, _, _ = build_feature_frame(sample, income)
        self.assertIn("other_expense", features.columns)
        result = train_and_compare(sample, income, save=False)
        self.assertTrue(result["ok"], result.get("message"))
        self.assertEqual(len(result["comparisons"]), 3)
        self.assertEqual(len(result["validation_actual"]), len(result["validation_predicted"]))
        self.assertTrue(all(row["mae"] >= 0 and row["rmse"] >= 0 for row in result["comparisons"]))
        artifact_path = Path(self.temp.name) / "models" / "model.joblib"
        expense_model.save_artifact(result, artifact_path)
        loaded = expense_model.load_artifact(artifact_path)
        self.assertEqual(loaded["model_name"], result["model_name"])
        self.assertEqual(loaded["versions"]["scikit_learn"], __import__("sklearn").__version__)

        loaded["versions"]["scikit_learn"] = "0.0"
        expense_model.save_artifact(loaded, artifact_path)
        with self.assertLogs("models.expense_model", level="WARNING"):
            with self.assertRaises(ArtifactLoadError):
                expense_model.load_artifact(artifact_path)

    def test_prediction_workflow_saves_real_forecast_and_rejects_corrupt_artifact(self) -> None:
        for month in range(1, 13):
            database.add_income(f"2025-{month:02d}-01", 45000, "Salary")
            database.add_expense(f"2025-{month:02d}-15", "Food", 1000 + month * 100, "UPI")
        model_path = Path(self.temp.name) / "models" / "expense_model.joblib"
        with patch.object(expense_model, "MODEL_PATH", model_path):
            trained = train_and_compare()
            self.assertTrue(trained["ok"], trained.get("message"))
            forecast = predict_next_month()
            self.assertTrue(forecast["ok"], forecast.get("message"))
            self.assertGreaterEqual(forecast["predicted_amount"], 0)
            saved = database.get_latest_prediction()
            self.assertEqual(saved["model_name"], forecast["model_name"])
            self.assertEqual(saved["prediction_month"], forecast["prediction_month"])
            database.add_expense("2026-01-15", "Food", 200, "UPI")
            with self.assertRaisesRegex(ArtifactLoadError, "Transactions changed"):
                predict_next_month()

        corrupt_path = Path(self.temp.name) / "corrupt.joblib"
        corrupt_path.write_bytes(b"not a joblib artifact")
        with self.assertLogs("models.expense_model", level="ERROR"):
            with self.assertRaises(ArtifactLoadError):
                expense_model.load_artifact(corrupt_path)

    def test_ollama_unavailable_is_nonfatal(self) -> None:
        with patch("ai.financial_assistant.requests.post", side_effect=requests.ConnectionError):
            answer, error = generate_financial_response({"expenses": 10}, "How can I save?")
        self.assertIsNone(answer)
        self.assertEqual(error, OLLAMA_UNAVAILABLE)

    def test_ollama_remote_override_is_rejected_without_network_call(self) -> None:
        with patch.dict("os.environ", {"OLLAMA_BASE_URL": "https://example.com"}):
            with patch("ai.financial_assistant.requests.post") as post:
                answer, error = generate_financial_response({"expenses": 10}, "How can I save?")
        self.assertIsNone(answer)
        self.assertEqual(error, LOCAL_ONLY_MESSAGE)
        post.assert_not_called()


if __name__ == "__main__":
    unittest.main()
