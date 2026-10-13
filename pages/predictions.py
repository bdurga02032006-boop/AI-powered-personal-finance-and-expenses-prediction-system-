import pandas as pd
import plotly.express as px
import streamlit as st

from analysis.spending_analysis import current_month_expense, monthly_summary
from database import database
from models.expense_model import load_artifact
from models.train_model import train_and_compare
from prediction.expense_predictor import predict_next_month


INSUFFICIENT_DATA = "Not enough historical data to make a reliable prediction."


def render() -> None:
    st.title("Expense Predictions")
    st.caption("Chronological holdout evaluation compares three regressors. Forecasts are estimates, not guarantees.")
    if st.button("Train and compare models", type="primary"):
        result = train_and_compare()
        if result["ok"]:
            st.session_state["training_result"] = result
            st.success(f"Selected {result['model_name']} using the lowest chronological validation RMSE.")
        else:
            st.warning(INSUFFICIENT_DATA)
    result = st.session_state.get("training_result")
    artifact = load_artifact()
    if result is None and artifact:
        result = artifact
    if result is None:
        st.info(INSUFFICIENT_DATA)
        st.caption("A reliable forecast requires at least nine distinct months of expenses.")
        return
    forecast = None
    if st.button("Predict next month", type="secondary"):
        forecast = predict_next_month()
        if forecast["ok"]:
            st.session_state["latest_forecast"] = forecast
        else:
            st.warning(forecast["message"])
    if forecast is None:
        forecast = st.session_state.get("latest_forecast")
    if forecast is None:
        forecast = predict_next_month()
        if not forecast["ok"]:
            forecast = None

    income, expenses = database.get_income(), database.get_expenses()
    today_month = pd.Timestamp.today().strftime("%Y-%m")
    current_expense = current_month_expense(expenses, today_month)
    predicted = forecast["predicted_amount"] if forecast else None
    percent_change = ((predicted - current_expense) / current_expense * 100) if predicted is not None and current_expense > 0 else None
    metrics = result["metrics"]
    columns = st.columns(5)
    columns[0].metric("Current month expense", f"₹{current_expense:,.2f}")
    columns[1].metric("Predicted next month", f"₹{predicted:,.2f}" if predicted is not None else "Not available")
    columns[2].metric("Expected change", f"{percent_change:+.1f}%" if percent_change is not None else "Not available")
    columns[3].metric("Selected model", result["model_name"])
    columns[4].metric("Validation MAE", f"₹{metrics['mae']:,.2f}")
    second = st.columns(3)
    second[0].metric("Validation RMSE", f"₹{metrics['rmse']:,.2f}")
    second[1].metric("Validation R²", f"{metrics['r2']:.3f}")
    second[2].metric("Months in training history", str(result.get("training_months", "Not available")))

    if result.get("comparisons"):
        st.subheader("Model comparison")
        st.dataframe(pd.DataFrame(result["comparisons"]).sort_values("rmse"), hide_index=True, use_container_width=True)
    if result.get("validation_actual"):
        actual_predicted = pd.DataFrame({
            "month": result["validation_months"],
            "Actual": result["validation_actual"],
            "Predicted": result["validation_predicted"],
        }).melt(id_vars="month", var_name="series", value_name="expense")
        st.plotly_chart(px.line(actual_predicted, x="month", y="expense", color="series", markers=True, title="Actual vs Predicted Expenses (Time-Aware Holdout)"), use_container_width=True)
    monthly = monthly_summary(income, expenses)
    if not monthly.empty:
        st.plotly_chart(px.line(monthly, x="month", y="expenses", markers=True, title="Historical Expense Trend"), use_container_width=True)
