from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

APP_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = APP_DIRECTORY / "AI-Personal-Finance"
TARGET_APP = PROJECT_DIRECTORY / "app.py"

if TARGET_APP.is_file():
    if str(PROJECT_DIRECTORY) not in sys.path:
        sys.path.insert(0, str(PROJECT_DIRECTORY))

    spec = spec_from_file_location("finance_project_app", TARGET_APP)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load project app from {TARGET_APP}")

    module = module_from_spec(spec)
    spec.loader.exec_module(module)
else:
    import streamlit as st

    st.title("Finance Project Not Found")
    st.error(f"Expected app at: {TARGET_APP}")
    st.info("Please start the project from the AI-Personal-Finance folder.")
