"""Fast local smoke tests for persistence, analysis, ML, and Ollama fallback."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import requests

from ai.financial_assistant import OLLAMA_UNAVAILABLE, generate_financial_response
from analysis.spending_analysis import budget_status
from database import database
from models import expense_model
from models.train_model import train_and_compare
from utils.helpers import finance_summary
from utils.preprocessing import build_feature_frame


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class FinanceSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.original_db_path = database.DB_PATH
        database.DB_PATH = Path(self.temporary_directory.name) / "finance.db"
        database.initialize_database()

    def tearDown(self) -> None:
        database.DB_PATH = self.original_db_path
        self.temporary_directory.cleanup()

    def test_schema_and_transaction_crud(self) -> None:
        with database.get_connection() as connection:
            table_names = {row["name"] for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertTrue({"users", "income", "expenses", "budgets", "predictions"}.issubset(table_names))

        income_id = database.add_income("2026-10-01", 50000, "Salary", "Monthly")
        expense_id = database.add_expense("2026-10-02", "Food", 900, "UPI", "Groceries")
        self.assertEqual(len(database.get_transactions()), 2)
        database.update_transaction("Expense", expense_id, "2026-10-03", 950, "Food", "UPI", "Groceries")
        self.assertEqual(float(database.get_expenses().iloc[0]["amount"]), 950)
        database.delete_transaction("Income", income_id)
        self.assertTrue(database.get_income().empty)

    def test_summary_and_budget_status(self) -> None:
        database.add_income("2026-10-01", 10000, "Salary")
        database.add_expense("2026-10-02", "Food", 900, "UPI")
        summary = finance_summary(database.get_income(), database.get_expenses())
        self.assertEqual(summary["savings"], 9100)
        database.save_budget("Food", "2026-10", 1000)
        database.save_budget("Food", "2026-10", 1100)
        status = budget_status(database.get_budgets("2026-10"), database.get_expenses(), "2026-10")
        self.assertEqual(len(status), 1)
        self.assertEqual(status.iloc[0]["status"], "Approaching Limit")

    def test_time_aware_model_training_and_artifact(self) -> None:
        sample = pd.read_csv(PROJECT_ROOT / "data" / "sample_expenses.csv")
        income = pd.DataFrame({"income_date": [f"2025-{month:02d}-01" for month in range(1, 13)], "amount": [45000] * 12})
        sample_features, _, _ = build_feature_frame(sample, income)
        self.assertIn("other_expense", sample_features.columns)
        result = train_and_compare(sample, income, save=False)
        self.assertTrue(result["ok"], result.get("message"))
        self.assertEqual(len(result["comparisons"]), 3)
        self.assertEqual(len(result["validation_actual"]), len(result["validation_predicted"]))
        self.assertTrue(all(row["mae"] >= 0 and row["rmse"] >= 0 for row in result["comparisons"]))

        artifact_path = Path(self.temporary_directory.name) / "models" / "model.joblib"
        expense_model.save_artifact(result, artifact_path)
        loaded = expense_model.load_artifact(artifact_path)
        self.assertEqual(loaded["model_name"], result["model_name"])

    def test_ollama_unavailable_is_nonfatal(self) -> None:
        with patch("ai.financial_assistant.requests.post", side_effect=requests.ConnectionError):
            answer, error = generate_financial_response({"expenses": 10}, "How can I save?")
        self.assertIsNone(answer)
        self.assertEqual(error, OLLAMA_UNAVAILABLE)


if __name__ == "__main__":
    unittest.main()