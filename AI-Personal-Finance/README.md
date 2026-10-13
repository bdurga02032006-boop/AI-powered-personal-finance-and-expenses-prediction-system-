# AI-Powered Personal Finance & Expense Prediction System

A local-first personal finance application for tracking income and expenses, understanding spending, planning category budgets, and comparing machine-learning models for next-month expense estimates. The UI, SQLite database, analysis, and predictions run locally. Optional AI responses use Ollama on this machine; the app rejects remote AI endpoints and makes no cloud or paid-service calls.

## Project Overview

```text
User input → Streamlit → SQLite → Pandas analysis → time-aware ML evaluation
           → next-month forecast → rule-based budget checks → optional local Ollama insights
```

## Problem Statement

People often record financial activity inconsistently and lack a simple view of cash flow, category spending, upcoming budget pressure, and likely near-term expenses. This application stores those records locally and derives its summaries and forecasts from that history.

## Objectives

- Record, view, edit, and delete income and expense transactions.
- Calculate income, expenses, savings, and savings percentage from stored records.
- Explore category totals and monthly spending/savings trends.
- Set monthly category budgets and flag approaching or exceeded limits.
- Compare three regressors with chronological validation and save the selected model.
- Offer optional natural-language insights through local Ollama.

## Features

- Dynamic Streamlit dashboard with financial metrics, Plotly charts, recent transactions, and budget alerts.
- Validated transaction forms and transaction editing/deletion.
- Monthly category budgets with utilization, remaining, exceeded amount, and status.
- Pandas analytics: category percentages, monthly spending/growth, and savings trend.
- Linear Regression, Random Forest, and Gradient Boosting comparison using holdout MAE, RMSE, and R².
- Joblib model persistence at `models/saved/expense_model.joblib`.
- Ollama integration sends only aggregate totals/category/budget summaries, never names, email addresses, or transaction descriptions.
- Sample CSV for demo use. It is not imported automatically into the live database.

## Architecture

- `app.py`: database initialization, navigation, and visual theme.
- `database/`: schema, SQLite connections, and parameterized data operations.
- `analysis/`: Pandas reports and rule-based budget status.
- `utils/`: input validation, data cleaning, aggregation, and feature engineering.
- `models/`: estimator definitions, time-aware comparison, and Joblib persistence.
- `prediction/`: forecast creation from the saved model and current history.
- `ai/`: local Ollama HTTP client and graceful failure handling.
- `pages/`: dashboard, transaction manager, analytics, predictions, budgets, and assistant.
- `data/sample_expenses.csv`: optional sample expenses for a disposable demonstration database.

## Technology Stack

Python 3.10+, Streamlit, SQLite (Python standard library), Pandas, NumPy, Scikit-learn, Plotly, Joblib, Requests, and optional Ollama.

## SQLite Database Structure

`finance.db` is created in the project root when the app starts. The schema defines:

- `users`: local user identity; one local profile is initialized automatically.
- `income`: dated income, source, and description.
- `expenses`: dated category expense, payment method, and description.
- `budgets`: one budget per user/category/month (unique constraint).
- `predictions`: forecast month, amount, and selected model.

Foreign keys are enabled for each connection. SQL values use parameters. Deletion table names are selected only from a fixed internal allowlist.

## ML Workflow

Daily expenses are cleaned and aggregated into continuous monthly totals and category totals. For each target month, features use only information available before the target: the previous three monthly expense totals, previous month's category totals and income, and the target calendar month number. The target is `next_month_total_expense`.

The latest chronological quarter (at least two observations) is held out; there is no random shuffle. Linear Regression, Random Forest Regressor, and Gradient Boosting Regressor are evaluated on that same time-ordered holdout. The model with the lowest observed validation RMSE is refit on all eligible history and saved along with its actual validation results. At least nine distinct expense months are required. Otherwise the app displays **Not enough historical data to make a reliable prediction.** MAE/RMSE are in INR; R² may be negative. Short histories make metrics uncertain.

The sample CSV is development/demo data and is not read automatically. If you import it for a presentation, use a disposable database and label the resulting forecast/metrics as sample-data results, not a user's actual finances.

## AI Workflow

Python calculates income, expenses, savings, savings percentage, category totals, current-month budget statuses, and a trained model forecast when available. The resulting aggregate JSON and question are sent to local Ollama at `http://localhost:11434` using `gemma3:4b` by default. Prompts instruct the model not to invent numbers. Local model outputs can still be inaccurate; verify advice independently. If Ollama is offline or errors, only the assistant response is unavailable; the rest of the application remains usable.

Optional settings:

```text
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:4b
```

`OLLAMA_BASE_URL` must use `localhost` or a loopback IP address. Remote hosts are rejected before a request is made. Ollama is optional; transaction tracking, analysis, budgets, and predictions work without it.

## Installation

Install Python 3.10 or newer. In PowerShell, from the project directory:

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Setup

No database setup is required: `finance.db` and the tables are created automatically on application startup. Begin by entering your actual records in Transactions. Do not combine sample CSV rows with personal records.

## How to Run

From the `AI-Personal-Finance` directory (create the environment first if needed with `python -m venv venv`):

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe -m streamlit run .\app.py
```

Streamlit opens the local application in a browser; use the sidebar to navigate. Launch from this directory rather than the workspace parent, which contains duplicate modules and pages.

The SQLite file is `finance.db` in this project directory. Model artifacts are written to `models/saved/expense_model.joblib` only after explicit training. Missing artifacts are normal before training; unreadable artifacts, artifacts made with a different scikit-learn version, or artifacts trained against changed transactions require retraining and never produce a stale forecast.

To configure the dashboard's low-balance alert threshold in PowerShell before launch:

```powershell
$env:FINANCE_LOW_BALANCE_THRESHOLD = "5000"
```

The default threshold is ₹0, so only a negative recorded net balance triggers that alert. Net balance is calculated from recorded income and expenses; the app does not connect to or track bank accounts.

## How to Train the ML Model

Enter at least nine distinct months of expenses, open **Predictions**, and select **Train and compare models**. The page reports measured chronological holdout metrics, selects by validation RMSE, and saves the model. Select **Predict next month** to calculate and record the estimate.

From PowerShell, training can also be run with:

```powershell
python -c "from models.train_model import train_and_compare; print(train_and_compare())"
```

## How to Start Ollama

Install Ollama separately, then run:

```powershell
ollama serve
ollama pull gemma3:4b
```

Open **AI Assistant** and ask about recorded financial summaries. Ollama is optional; all other features work without it.

## ML Evaluation Metrics

- **MAE**: mean absolute forecast error, in INR; lower is better.
- **RMSE**: square root of mean squared error, in INR; lower is better and large errors count more.
- **R²**: proportion of target variance explained on holdout; higher is generally better and negative values are possible.

Metrics are computed only from the local transaction history used for training; no performance values are hardcoded.

## Limitations

- Single local profile; not a hosted multi-user service.
- Short/irregular history makes predictions uncertain; the minimum data check cannot ensure forecast accuracy.
- Inflation, known future events, and future income changes are not modeled unless reflected in historical features.
- Ollama responses are informational, not professional financial advice.
- Protect and back up the local SQLite and model files.

## Future Enhancements

- Encrypted backups and configurable import/export.
- Recurring transaction support and richer cash-flow forecasting.
- Optional authentication for multi-user deployments.
- Rolling-origin evaluation and model drift monitoring with longer history.
- Local model selection and additional AI response checks.
