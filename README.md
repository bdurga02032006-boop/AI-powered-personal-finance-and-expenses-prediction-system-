# AI-Powered Personal Finance & Expense Prediction System

A local-first personal finance application for recording income and expenses, understanding spending, planning category budgets, and comparing machine-learning models for a next-month expense estimate. The Streamlit UI and SQLite database run on your computer. Optional AI responses use an Ollama model on your local machine.

## Project Overview

The project connects user-entered records to reproducible reporting and an ML workflow:

```text
User input → Streamlit → SQLite → Pandas analysis → time-aware ML evaluation
           → next-month forecast → rule-based budget checks → optional local Ollama insights
```

## Problem Statement

People often record financial activity inconsistently and lack a simple view of cash flow, category spending, upcoming budget pressure, and likely near-term expenses. This application keeps those records in a local database and derives its summaries and forecasts from that history.

## Objectives

- Record, view, edit, and delete income and expense transactions.
- Calculate income, expenses, savings, and savings percentage from stored records.
- Explore category totals and monthly spending/savings trends.
- Set monthly category budgets and flag approaching or exceeded limits.
- Compare three regressors using chronological validation and save the best model.
- Offer optional natural-language insights through a local Ollama service.

## Features

- Streamlit dashboard with dynamically calculated metrics, charts, recent transactions, and budget alerts.
- Income and expense forms with date, positive-amount, required-field, and length validation.
- Transaction editing/deletion and monthly category budget upsert/removal.
- Interactive Plotly charts and Pandas analytics.
- Linear Regression, Random Forest Regressor, and Gradient Boosting Regressor comparison.
- Time-ordered holdout MAE, RMSE, and R²; selection is by lowest holdout RMSE.
- Model artifact saved to `models/saved/expense_model.joblib`.
- Ollama calls contain aggregate totals and category/budget summaries only, not names, email addresses, or transaction descriptions.
- Sample CSV for demonstration; it is never imported into the live database automatically.

## Architecture

- `app.py`: initializes the database and handles navigation.
- `database/`: SQLite schema, connection management, and parameterized operations.
- `analysis/`: Pandas spending and budget calculations.
- `utils/`: reusable validation, cleaning, aggregation, and ML feature generation.
- `models/`: estimator definitions, chronological evaluation, and Joblib persistence.
- `prediction/`: forecast creation from the saved model and current database history.
- `ai/`: local Ollama HTTP integration and failure handling.
- `pages/`: dashboard, transaction manager, analytics, prediction, budget, and AI views.
- `data/sample_expenses.csv`: optional demonstration expense rows.

## Technology Stack

Python 3.10+, Streamlit, SQLite (Python standard library), Pandas, NumPy, Scikit-learn, Plotly, Joblib, Requests, and Ollama (optional).

## SQLite Database Structure

`finance.db` is created in the project root the first time the app starts. The schema defines:

- `users`: local user identity; a local-only profile is initialized automatically.
- `income`: dated income records and source.
- `expenses`: dated category expenses and payment method.
- `budgets`: one category budget per user and month (unique constraint).
- `predictions`: saved forecast amount, month, and selected model.

All foreign keys are enabled for each SQLite connection. All variable SQL values use parameters; table/column identifiers used for transaction deletion are selected only from a fixed internal allowlist.

## ML Workflow

Daily expenses are cleaned and aggregated into continuous monthly totals and category totals. Features for a target month use only the three preceding months, income and category mix from the most recently observed month, and the target calendar month number. The target is `next_month_total_expense`. Models are evaluated on the latest chronological quarter (at least two holdout months); the model with lowest holdout RMSE is then refit on all available training examples and persisted with its validation predictions and metrics. No random shuffle is used.

At least nine distinct months of expense history are required before a model is evaluated. When the history is too short, the app displays: **Not enough historical data to make a reliable prediction.** MAE and RMSE are in the database currency (INR); R² is calculated on the chronological holdout and can be negative. A small personal history makes all validation metrics uncertain.

The included CSV is for development/demo only and is not loaded automatically. If used for a project demonstration, import it explicitly into a disposable database and clearly label it as sample data; do not interpret its metrics as a user's real financial results.

## AI Workflow

Python calculates the financial totals, category totals, current-month budget statuses, and (when trained) model forecast. The resulting aggregate JSON and the user's question are sent to Ollama at `http://localhost:11434` using `gemma3:4b` by default. No identity fields or transaction descriptions are included. The prompt instructs the model not to invent data, but local language models can still make mistakes; verify any advice. If Ollama is offline or returns an error, the app shows a friendly availability message and other pages continue to work.

Optional environment settings:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

## Installation

Install Python 3.10 or newer. In PowerShell, from this project folder:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Setup

No database setup is required. `finance.db` and all tables are created automatically on app startup. Start with an empty database and enter your actual records in Transactions. To demonstrate with sample records, copy/import the CSV rows intentionally; never mix sample data with personal records.

## How to Run

```powershell
streamlit run app.py
```

Streamlit opens the app in your browser. Navigation is in the sidebar.

## How to Train the ML Model

Enter at least nine distinct months of expenses. Open **Predictions** and select **Train and compare models**. The model comparison uses a chronological holdout, reports its measured metrics, selects by validation RMSE, and saves the fitted artifact. Select **Predict next month** to save and display the forecast. The training page does not fabricate a forecast when history is insufficient.

You can also train through Python from the project root:

```powershell
python -c "from models.train_model import train_and_compare; print(train_and_compare())"
```

## How to Start Ollama

Install Ollama separately, then run:

```powershell
ollama serve
ollama pull gemma3:4b
```

Open **AI Assistant** in the app and ask a question about your recorded summaries. Ollama is optional; finance tracking, analysis, budgets, and predictions do not depend on it.

## ML Evaluation Metrics

- **MAE**: mean absolute forecast error, in INR; lower is better.
- **RMSE**: square root of mean squared error, in INR; lower is better and larger misses are penalized more.
- **R²**: proportion of target variance explained on the holdout; higher is generally better, and negative values are possible.

Only metrics calculated from the local user's actual stored history are shown.

## Limitations

- This is a single local profile, not a multi-user hosted service.
- Short and irregular histories make forecasting unreliable; the UI enforces a minimum history but cannot guarantee accuracy.
- Forecasts do not model inflation, known future events, or changes in income unless those patterns exist in the recorded features.
- Ollama answers are generated locally but can still be inaccurate; they are informational, not professional financial advice.
- `finance.db` and model artifacts are local files; protect the machine and back up data securely.

## Future Enhancements

- Optional encrypted backups and configurable data export/import.
- Recurring transaction support and richer cash-flow forecasting.
- Per-user authentication for a multi-user deployment.
- Model drift monitoring and broader rolling-origin evaluation when enough history is available.
- Local Ollama model selection and response quality checks.
