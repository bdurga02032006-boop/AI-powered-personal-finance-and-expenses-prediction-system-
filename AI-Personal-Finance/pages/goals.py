import streamlit as st


def render() -> None:
    st.title("Goals")
    st.caption("A clear view of the goals you choose to work toward.")
    with st.container(border=True):
        st.subheader("No financial goals to show")
        st.write(
            "Goal tracking is not connected to the local database yet, so no sample balances or progress "
            "are displayed here."
        )
