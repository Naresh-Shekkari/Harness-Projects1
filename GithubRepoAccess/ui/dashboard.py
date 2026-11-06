"""Dashboard layout and UI component orchestration for Streamlit."""

from datetime import datetime
from typing import Any, Optional
import pandas as pd
from pandas.io.formats.style import Styler
import streamlit as st

from config.settings import (
    APP_SUBTITLE,
    APP_TITLE,
    AccessStatus,
    COL_ACCESS_STATUS,
    COL_HTTP_STATUS,
    COL_VALIDATION_MESSAGE,
)
from services.excel_service import ExcelService, ExcelValidationError
from services.github_service import GitHubAuthException, GitHubService
from services.validation_service import ValidationService
from ui.styles import CUSTOM_CSS, render_header, render_kpi_cards
from utils.logger import get_logger

logger = get_logger(__name__)


def apply_table_styles(df: pd.DataFrame) -> Styler:
    """Apply visual status highlights to the DataFrame for dashboard display.

    Args:
        df: Filtered DataFrame to display.

    Returns:
        Pandas Styler object with colored status cells.
    """
    def highlight_status(row: pd.Series) -> list:
        status = str(row.get(COL_ACCESS_STATUS, "")).strip()
        styles = [""] * len(row)
        if COL_ACCESS_STATUS in row.index:
            status_idx = row.index.get_loc(COL_ACCESS_STATUS)
            if status == AccessStatus.ABLE_TO_ACCESS.value:
                styles[status_idx] = "background-color: #D1FAE5; color: #065F46; font-weight: bold;"
            elif status == AccessStatus.NOT_ACCESSIBLE.value:
                styles[status_idx] = "background-color: #FEE2E2; color: #991B1B; font-weight: bold;"
            elif status == AccessStatus.VALIDATION_ERROR.value:
                styles[status_idx] = "background-color: #FEF3C7; color: #92400E; font-weight: bold;"
        return styles

    return df.style.apply(highlight_status, axis=1)


class DashboardApp:
    """Main Streamlit Dashboard Application controller."""

    def __init__(self):
        """Initialize required services and session states."""
        self.excel_service = ExcelService()
        self.github_service = GitHubService()
        self.validation_service = ValidationService(github_service=self.github_service)

    def init_session_state(self) -> None:
        """Initialize session state keys if not already present."""
        defaults = {
            "uploaded_df": None,
            "repo_col": None,
            "url_col": None,
            "file_name": None,
            "token_valid": False,
            "token_user_info": None,
            "results_df": None,
            "summary_stats": None,
            "auth_error": None,
        }
        for key, val in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = val

    def render(self) -> None:
        """Render the complete dashboard interface."""
        self.init_session_state()

        # Inject custom SaaS styling CSS
        st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

        # Main Header Banner
        st.markdown(render_header(APP_TITLE, APP_SUBTITLE), unsafe_allow_html=True)

        # -----------------------------------------------------------------
        # SECTION 1 & 2: TWO-COLUMN CONFIGURATION (Upload & Authentication)
        # -----------------------------------------------------------------
        col_upload, col_auth = st.columns([1.1, 1], gap="large")

        with col_upload:
            st.markdown(
                """
                <div class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                    1. Upload Repository Spreadsheet
                </div>
                <div class="section-subtitle">Select an Excel (.xlsx or .xls) file containing repository details.</div>
                """,
                unsafe_allow_html=True,
            )

            uploaded_file = st.file_uploader(
                "Upload Excel Spreadsheet",
                type=["xlsx", "xls"],
                key="repo_file_uploader",
                help="Accepts .xlsx or .xls files with repository name and GitHub URL columns.",
                label_visibility="collapsed",
            )

            if uploaded_file is not None:
                if st.session_state["file_name"] != uploaded_file.name:
                    try:
                        df, repo_col, url_col = self.excel_service.load_and_validate_input(
                            uploaded_file.getvalue()
                        )
                        st.session_state["uploaded_df"] = df
                        st.session_state["repo_col"] = repo_col
                        st.session_state["url_col"] = url_col
                        st.session_state["file_name"] = uploaded_file.name
                        # Reset prior results on new file upload
                        st.session_state["results_df"] = None
                        st.session_state["summary_stats"] = None
                        st.toast(f"Successfully loaded {len(df)} repositories from {uploaded_file.name}", icon="📁")
                    except ExcelValidationError as err:
                        st.error(f"Excel Validation Error: {str(err)}. Please correct and try again.")
                        st.session_state["uploaded_df"] = None

            if st.session_state["uploaded_df"] is not None:
                df = st.session_state["uploaded_df"]
                st.success(
                    f"**{st.session_state['file_name']}** loaded successfully, ({len(df)} repositories detected)\n\n"
                    f"Mapped Columns: `{st.session_state['repo_col']}` | `{st.session_state['url_col']}`"
                )
                with st.expander("Preview Uploaded Excel Data", expanded=False):
                    st.dataframe(df.head(10), use_container_width=True)

        with col_auth:
            st.markdown(
                """
                <div class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2">
                        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect>
                        <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
                    </svg>
                    2. GitHub Authentication
                </div>
                <div class="section-subtitle">Provide a GitHub Personal Access Token (PAT) with repository read access.</div>
                """,
                unsafe_allow_html=True,
            )

            pat_input = st.text_input(
                "GitHub Personal Access Token (PAT)",
                type="password",
                key="pat_input_field",
                placeholder="ghp_... or github_pat_...",
                help="Your token is kept only in server-side session memory for this run and never stored or logged.",
            )

            btn_col1, btn_col2 = st.columns([1, 1.5])
            with btn_col1:
                if st.button("Test Connection", use_container_width=True):
                    if not pat_input:
                        st.warning("Please enter a GitHub PAT first.")
                    else:
                        with st.spinner("Connecting to GitHub API..."):
                            is_valid, user_data, msg = self.github_service.validate_token(pat_input)
                            st.session_state["token_valid"] = is_valid
                            st.session_state["token_user_info"] = user_data
                            if is_valid:
                                st.session_state["auth_error"] = None
                                st.success(msg + '');
                            else:
                                st.session_state["auth_error"] = msg
                                st.error(msg)

            with btn_col2:
                if st.session_state["token_valid"] and st.session_state["token_user_info"]:
                    user_login = st.session_state["token_user_info"].get("login", "User")
                    st.markdown(
                        f"""
                        <div style="padding-top: 0.35rem;">
                            <span class="badge badge-green">✓ Verified as @{user_login}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                elif st.session_state["auth_error"]:
                    st.markdown(
                        """
                        <div style="padding-top: 0.35rem;">
                            <span class="badge badge-red">✗ Authentication Failed</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            st.markdown(
                """
                <div class="security-notice">
                    🔒 <strong>Security Guarantee:</strong> The PAT is stored in server-side application memory
                    strictly for the current execution. It is never logged, never stored in Excel or databases,
                    and never exposed to client-side scripts.
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

        # -----------------------------------------------------------------
        # SECTION 3: EXECUTE VALIDATION
        # -----------------------------------------------------------------
        st.markdown(
            """
            <div class="section-title">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2">
                    <polygon points="5 3 19 12 5 21 5 3"></polygon>
                </svg>
                3. Execute Access Validation
            </div>
            <div class="section-subtitle">Run automated HTTP REST API checks against each repository.</div>
            """,
            unsafe_allow_html=True,
        )

        can_validate = (st.session_state["uploaded_df"] is not None) and bool(pat_input)

        if not can_validate:
            reasons = []
            if st.session_state["uploaded_df"] is None:
                reasons.append("upload an Excel file")
            if not pat_input:
                reasons.append("enter a GitHub Personal Access Token")
            st.info(f"To begin validation, please { ' and '.join(reasons)} above.")

        start_btn = st.button(
            "START REPOSITORY VALIDATION",
            type="primary",
            disabled=not can_validate,
            use_container_width=True,
        )

        if start_btn:
            df = st.session_state["uploaded_df"]
            repo_col = st.session_state["repo_col"]
            url_col = st.session_state["url_col"]
            total_count = len(df)

            # Containers for live progress
            progress_card = st.empty()
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(current_idx: int, total: int, repo_name: str, status: Optional[str]):
                pct = min(int((current_idx / total) * 100), 100) if total > 0 else 0
                progress_bar.progress(pct)
                status_icon = "🔄"
                if status == AccessStatus.ABLE_TO_ACCESS.value:
                    status_icon = "✅"
                elif status == AccessStatus.NOT_ACCESSIBLE.value:
                    status_icon = "❌"
                elif status == AccessStatus.VALIDATION_ERROR.value:
                    status_icon = "⚠️"

                status_text.markdown(
                    f"**{status_icon} Processing {current_idx} of {total}:** `{repo_name}` ({pct}%)"
                )

            try:
                with st.spinner("Validating repository access via GitHub REST API..."):
                    results_df, summary = self.validation_service.validate_repositories(
                        df=df,
                        repo_col=repo_col,
                        url_col=url_col,
                        token=pat_input,
                        progress_callback=update_progress,
                    )
                st.session_state["results_df"] = results_df
                st.session_state["summary_stats"] = summary
                progress_bar.progress(100)
                status_text.success("🎉 Repository validation completed successfully!")
                st.toast("Validation run complete!", icon="🚀")

            except GitHubAuthException as auth_err:
                progress_bar.empty()
                status_text.empty()
                st.error(
                    f"🚫 **Authentication Halted:** {str(auth_err)}\n\n"
                    "The GitHub Personal Access Token supplied was rejected (HTTP 401 Unauthorized). "
                    "Validation has been stopped immediately to avoid marking repositories incorrectly. "
                    "Please provide a valid PAT and re-run."
                )

            except Exception as exc:
                progress_bar.empty()
                status_text.empty()
                st.error(f"An unexpected error occurred during validation: {str(exc)}")
                logger.exception("Unexpected error in validation execution")

        # -----------------------------------------------------------------
        # SECTION 4: DASHBOARD RESULTS & METRICS
        # -----------------------------------------------------------------
        if st.session_state["results_df"] is not None:
            results_df = st.session_state["results_df"]
            summary = st.session_state["summary_stats"]

            st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563EB" stroke-width="2">
                        <line x1="18" y1="20" x2="18" y2="10"></line>
                        <line x1="12" y1="20" x2="12" y2="4"></line>
                        <line x1="6" y1="20" x2="6" y2="14"></line>
                    </svg>
                    4. Validation Results & Metrics
                </div>
                <div class="section-subtitle">Review verification breakdown and filter individual repository statuses.</div>
                """,
                unsafe_allow_html=True,
            )

            # 4 KPI Summary Cards
            st.markdown(
                render_kpi_cards(
                    total=summary["total"],
                    accessible=summary["accessible"],
                    not_accessible=summary["not_accessible"],
                    errors=summary["errors"],
                    success_rate=summary["success_rate"],
                ),
                unsafe_allow_html=True,
            )

            # Filtering and Search controls
            filter_col, search_col = st.columns([1.5, 2])
            with filter_col:
                selected_filter = st.selectbox(
                    "Filter by Access Status",
                    options=[
                        "All",
                        AccessStatus.ABLE_TO_ACCESS.value,
                        AccessStatus.NOT_ACCESSIBLE.value,
                        AccessStatus.VALIDATION_ERROR.value,
                    ],
                    key="status_filter_selector",
                )

            with search_col:
                search_query = st.text_input(
                    "Search Repositories",
                    placeholder="Search by name, URL, or owner...",
                    key="repo_search_input",
                )

            # Filter data
            filtered_df = results_df.copy()
            if selected_filter != "All":
                filtered_df = filtered_df[filtered_df[COL_ACCESS_STATUS] == selected_filter]

            if search_query:
                query = search_query.strip().lower()
                # Search across all string columns
                mask = filtered_df.astype(str).apply(
                    lambda row: row.str.lower().str.contains(query, regex=False).any(), axis=1
                )
                filtered_df = filtered_df[mask]

            st.caption(f"Showing **{len(filtered_df)}** of **{len(results_df)}** repositories")

            # Display styled table
            st.dataframe(
                apply_table_styles(filtered_df),
                use_container_width=True,
                height=380,
            )

            # -----------------------------------------------------------------
            # SECTION 5: DOWNLOAD REPORT
            # -----------------------------------------------------------------
            st.markdown("<div style='margin-top: 1.5rem;'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class="section-title">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                        <polyline points="7 10 12 15 17 10"></polyline>
                        <line x1="12" y1="15" x2="12" y2="3"></line>
                    </svg>
                    5. Download Validated Excel Report
                </div>
                <div class="section-subtitle">
                    Export the complete spreadsheet with original data, validation statuses, color styling, and an Executive Summary sheet.
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.spinner("Generating styled Excel report with openpyxl..."):
                excel_bytes = self.excel_service.generate_excel_report(
                    results_df=results_df, summary_stats=summary
                )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_filename = f"github_repo_access_report_{timestamp}.xlsx"

            st.download_button(
                label="📥 DOWNLOAD VALIDATED EXCEL REPORT",
                data=excel_bytes,
                file_name=report_filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
