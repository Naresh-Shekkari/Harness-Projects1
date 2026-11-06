"""Main application entry point for the GitHub Repository Access Validator."""

import streamlit as st
from ui.dashboard import DashboardApp
from config.settings import APP_TITLE

# Set Streamlit page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main():
    """Run the Streamlit Dashboard application."""
    app = DashboardApp()
    app.render()


if __name__ == "__main__":
    main()
