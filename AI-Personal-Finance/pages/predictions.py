import pandas as pd
import plotly.express as px
import streamlit as st
import logging

from analysis.spending_analysis import current_month_expense, monthly_summary
from database import database
from models.expense_model import ArtifactLoadError, load_artifact
from models.train_model import train_and_compare
from prediction.expense_predictor import predict_next_month


INSUFFICIENT_DATA = "Not enough historical data to make a reliable prediction."
logger = logging.getLogger(__name__)


def render() -> None:
    st.title("Expense Predictions")
    st.caption("Chronological holdout evaluation compares three regressors. Forecasts are estimates, not guarantees.")
    if st.button("Train and compare models", type="primary"):
        try:
            result = train_and_compare()
        except OSError:
            logger.exception("Unable to save the trained prediction model.")
            st.error("The model could not be saved locally. Check that the project folder is writable.")
            result = None
        if result and result["ok"]:
            st.session_state["training_result"] = result
            st.success(f"Selected {result['model_name']} using the lowest chronological validation RMSE.")
        elif result:
            st.warning(INSUFFICIENT_DATA)
    result = st.session_state.get("training_result")
    artifact_error = False
    if result is None:
        try:
            result = load_artifact()
        except ArtifactLoadError as error:
            st.error(str(error))
            artifact_error = True
    if not result:
        if not artifact_error:
            st.info(INSUFFICIENT_DATA)
            st.caption("A reliable forecast requires at least nine distinct months of expenses.")
        return
    if st.button("Predict next month"):
        try:
            forecast = predict_next_month()
            if forecast["ok"]:
                st.session_state["latest_forecast"] = forecast
            else:
                st.warning(forecast["message"])
        except ArtifactLoadError as error:
            st.error(str(error))
    forecast = st.session_state.get("latest_forecast")
    income, expenses = database.get_income(), database.get_expenses()
    current = current_month_expense(expenses, pd.Timestamp.today().strftime("%Y-%m"))
    predicted = forecast["predicted_amount"] if forecast else None
    change = (predicted - current) / current * 100 if predicted is not None and current > 0 else None
    metrics = result["metrics"]
    cards = st.columns(5)
    cards[0].metric("Current month expense", f"₹{current:,.2f}")
    cards[1].metric("Predicted next month", f"₹{predicted:,.2f}" if predicted is not None else "Not available")
    cards[2].metric("Expected change", f"{change:+.1f}%" if change is not None else "Not available")
    cards[3].metric("Selected model", result["model_name"])
    cards[4].metric("Validation MAE", f"₹{metrics['mae']:,.2f}")
    rest = st.columns(3)
    rest[0].metric("Validation RMSE", f"₹{metrics['rmse']:,.2f}")
    rest[1].metric("Validation R²", f"{metrics['r2']:.3f}")
    rest[2].metric("Months in history", str(result.get("training_months", "Not available")))
    st.subheader("Model comparison")
    st.dataframe(pd.DataFrame(result["comparisons"]).sort_values("rmse"), hide_index=True, width="stretch")
    if result.get("validation_actual"):
        chart = pd.DataFrame({"month": result["validation_months"], "Actual": result["validation_actual"],
                              "Predicted": result["validation_predicted"]}).melt(id_vars="month", var_name="series", value_name="expense")
        st.plotly_chart(px.line(chart, x="month", y="expense", color="series", markers=True,
                                title="Actual vs Predicted Expenses (Time-Aware Holdout)"), width="stretch")
    monthly = monthly_summary(income, expenses)
    if not monthly.empty:
        st.plotly_chart(px.line(monthly, x="month", y="expenses", markers=True, title="Historical Expense Trend"), width="stretch")
