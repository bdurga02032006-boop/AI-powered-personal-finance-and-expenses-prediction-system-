import streamlit as st


def render() -> None:
    st.title("Goals")
    st.caption("Track progress toward your financial milestones.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Emergency Fund", "₹45,000", "+₹8,000")
    with col2:
        st.metric("Vacation Fund", "₹18,500", "+₹2,500")
    with col3:
        st.metric("Home Down Payment", "₹62,000", "+₹11,000")

    st.markdown("---")
    st.write("Set and monitor financial goals from this section while preserving the rest of the dashboard behavior.")
