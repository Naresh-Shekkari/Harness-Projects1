"""Excel processing and report generation service.

Handles reading, validating, and parsing repository input files, as well as
generating production-quality styled Excel reports with openpyxl.
"""

import io
from datetime import datetime
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
import pandas as pd

from config.settings import (
    AccessStatus,
    COL_ACCESS_STATUS,
    COL_HTTP_STATUS,
    COL_VALIDATION_MESSAGE,
    COLOR_DANGER_FILL,
    COLOR_DANGER_FONT,
    COLOR_HEADER_FILL,
    COLOR_HEADER_FONT,
    COLOR_SUCCESS_FILL,
    COLOR_SUCCESS_FONT,
    COLOR_WARNING_FILL,
    COLOR_WARNING_FONT,
    COLOR_ZEBRA_FILL,
    REPO_NAME_ALIASES,
    REPO_URL_ALIASES,
)
from utils.logger import get_logger
from utils.validators import find_matching_column

logger = get_logger(__name__)


class ExcelValidationError(Exception):
    """Raised when an uploaded Excel file fails structure validation."""
    pass


class ExcelService:
    """Service for parsing and producing Excel files."""

    @staticmethod
    def load_and_validate_input(
        file_input: Union[str, bytes, BinaryIO]
    ) -> Tuple[pd.DataFrame, str, str]:
        """Load and validate repository spreadsheet.

        Accepts .xlsx and .xls formats. Automatically detects and matches column
        headers with reasonable variations.

        Args:
            file_input: File path, bytes, or file-like object.

        Returns:
            Tuple of (DataFrame, repo_column_name, url_column_name).

        Raises:
            ExcelValidationError: If mandatory columns are missing or file is invalid.
        """
        try:
            # Read first sheet
            if isinstance(file_input, bytes):
                df = pd.read_excel(io.BytesIO(file_input))
            else:
                df = pd.read_excel(file_input)
        except Exception as exc:
            logger.error("Failed to read Excel file: %s", str(exc))
            raise ExcelValidationError(f"Unable to read Excel file: {str(exc)}") from exc

        if df.empty:
            raise ExcelValidationError("The uploaded Excel spreadsheet is completely empty.")

        # Drop rows where every single column is empty
        df = df.dropna(how="all").reset_index(drop=True)
        if df.empty:
            raise ExcelValidationError("All rows in the uploaded spreadsheet are blank.")

        columns = [str(c).strip() for c in df.columns]

        # Identify repository name column
        repo_col = find_matching_column(columns, REPO_NAME_ALIASES)
        # Identify repository URL column
        url_col = find_matching_column(columns, REPO_URL_ALIASES)

        missing = []
        if not repo_col:
            missing.append("Repository Name (aliases: 'Repo Name', 'Repository', 'Repo')")
        if not url_col:
            missing.append("GitHub URL (aliases: 'Repository URL', 'Git URL', 'Repo URL', 'URL')")

        if missing:
            found_cols = ", ".join([f"'{c}'" for c in columns])
            raise ExcelValidationError(
                f"Missing required column(s): {'; '.join(missing)}. "
                f"Columns detected in file: [{found_cols}]."
            )

        logger.info(
            "Excel validated successfully. %d rows detected. Repo col: '%s', URL col: '%s'.",
            len(df),
            repo_col,
            url_col,
        )
        return df, repo_col, url_col

    @staticmethod
    def generate_excel_report(
        results_df: pd.DataFrame,
        summary_stats: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        """Create a polished, styled multi-sheet Excel report with openpyxl.

        Sheet 1: 'Validation Results' with status color fills and preserved data.
        Sheet 2: 'Executive Summary' with high-level statistics and metadata.

        Args:
            results_df: DataFrame containing original data plus validation columns.
            summary_stats: Optional dictionary containing totals, counts, and rates.

        Returns:
            Bytes containing the generated .xlsx workbook.
        """
        wb = openpyxl.Workbook()

        # Styles definition
        header_fill = PatternFill(
            start_color=COLOR_HEADER_FILL, end_color=COLOR_HEADER_FILL, fill_type="solid"
        )
        header_font = Font(name="Segoe UI", size=11, bold=True, color=COLOR_HEADER_FONT)
        data_font = Font(name="Segoe UI", size=10)
        bold_font = Font(name="Segoe UI", size=10, bold=True)

        success_fill = PatternFill(
            start_color=COLOR_SUCCESS_FILL, end_color=COLOR_SUCCESS_FILL, fill_type="solid"
        )
        success_font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_SUCCESS_FONT)

        danger_fill = PatternFill(
            start_color=COLOR_DANGER_FILL, end_color=COLOR_DANGER_FILL, fill_type="solid"
        )
        danger_font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_DANGER_FONT)

        warning_fill = PatternFill(
            start_color=COLOR_WARNING_FILL, end_color=COLOR_WARNING_FILL, fill_type="solid"
        )
        warning_font = Font(name="Segoe UI", size=10, bold=True, color=COLOR_WARNING_FONT)

        zebra_fill = PatternFill(
            start_color=COLOR_ZEBRA_FILL, end_color=COLOR_ZEBRA_FILL, fill_type="solid"
        )

        thin_border = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )

        # -------------------------------------------------------------
        # SHEET 1: Validation Results
        # -------------------------------------------------------------
        ws_results = wb.active
        ws_results.title = "Validation Results"
        ws_results.views.sheetView[0].showGridLines = True

        # Write header row
        headers = list(results_df.columns)
        for col_idx, header in enumerate(headers, start=1):
            cell = ws_results.cell(row=1, column=col_idx, value=str(header))
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        ws_results.row_dimensions[1].height = 28

        # Identify key validation column indices (1-based)
        status_col_idx = headers.index(COL_ACCESS_STATUS) + 1 if COL_ACCESS_STATUS in headers else -1
        http_col_idx = headers.index(COL_HTTP_STATUS) + 1 if COL_HTTP_STATUS in headers else -1

        # Write data rows
        for row_idx, row_data in enumerate(results_df.itertuples(index=False), start=2):
            ws_results.row_dimensions[row_idx].height = 22
            is_zebra = (row_idx % 2 == 0)

            for col_idx, value in enumerate(row_data, start=1):
                # Clean NaNs to empty strings
                val = "" if pd.isna(value) else value
                cell = ws_results.cell(row=row_idx, column=col_idx, value=val)
                cell.font = data_font
                cell.border = thin_border
                cell.alignment = Alignment(vertical="center")

                # Default background zebra striping
                if is_zebra:
                    cell.fill = zebra_fill

                # Special formatting for Access Status column
                if col_idx == status_col_idx:
                    status_str = str(val).strip()
                    if status_str == AccessStatus.ABLE_TO_ACCESS.value:
                        cell.fill = success_fill
                        cell.font = success_font
                    elif status_str == AccessStatus.NOT_ACCESSIBLE.value:
                        cell.fill = danger_fill
                        cell.font = danger_font
                    elif status_str == AccessStatus.VALIDATION_ERROR.value:
                        cell.fill = warning_fill
                        cell.font = warning_font
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                # Center align HTTP status code
                elif col_idx == http_col_idx:
                    cell.alignment = Alignment(horizontal="center", vertical="center")

        # Auto-fit column widths with readable padding
        for col in ws_results.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                cell_value = str(cell.value or "")
                # Limit length calculation to 60 for multiline wrap
                max_len = max(max_len, min(len(cell_value), 60))
            ws_results.column_dimensions[col_letter].width = max(max_len + 4, 14)

        # -------------------------------------------------------------
        # SHEET 2: Executive Summary
        # -------------------------------------------------------------
        ws_summary = wb.create_sheet(title="Executive Summary")
        ws_summary.views.sheetView[0].showGridLines = True

        # Summary Title Header
        title_font = Font(name="Segoe UI", size=16, bold=True, color="1E293B")
        ws_summary.cell(row=2, column=2, value="GitHub Repository Access Validation Summary").font = title_font
        ws_summary.cell(
            row=3,
            column=2,
            value=f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Harness Migration Phase 1",
        ).font = Font(name="Segoe UI", size=10, italic=True, color="64748B")

        # Compute or use stats
        total = len(results_df)
        accessible = (
            (results_df[COL_ACCESS_STATUS] == AccessStatus.ABLE_TO_ACCESS.value).sum()
            if COL_ACCESS_STATUS in results_df
            else 0
        )
        not_accessible = (
            (results_df[COL_ACCESS_STATUS] == AccessStatus.NOT_ACCESSIBLE.value).sum()
            if COL_ACCESS_STATUS in results_df
            else 0
        )
        errors = (
            (results_df[COL_ACCESS_STATUS] == AccessStatus.VALIDATION_ERROR.value).sum()
            if COL_ACCESS_STATUS in results_df
            else 0
        )
        rate = f"{(accessible / total * 100):.1f}%" if total > 0 else "0.0%"

        summary_rows = [
            ("Total Repositories Evaluated", total, None, None),
            ("Able to Access (Ready for Migration)", accessible, success_fill, success_font),
            ("Not Accessible (Action Required)", not_accessible, danger_fill, danger_font),
            ("Validation Errors / Rate Limited", errors, warning_fill, warning_font),
            ("Access Success Rate", rate, None, bold_font),
        ]

        # Table header
        ws_summary.cell(row=5, column=2, value="Metric").font = header_font
        ws_summary.cell(row=5, column=2).fill = header_fill
        ws_summary.cell(row=5, column=2).alignment = Alignment(horizontal="left", vertical="center")
        ws_summary.cell(row=5, column=2).border = thin_border

        ws_summary.cell(row=5, column=3, value="Value").font = header_font
        ws_summary.cell(row=5, column=3).fill = header_fill
        ws_summary.cell(row=5, column=3).alignment = Alignment(horizontal="center", vertical="center")
        ws_summary.cell(row=5, column=3).border = thin_border
        ws_summary.row_dimensions[5].height = 24

        curr_row = 6
        for label, val, fill, font in summary_rows:
            ws_summary.row_dimensions[curr_row].height = 22
            c_label = ws_summary.cell(row=curr_row, column=2, value=label)
            c_label.font = data_font
            c_label.border = thin_border
            c_label.alignment = Alignment(vertical="center")

            c_val = ws_summary.cell(row=curr_row, column=3, value=val)
            c_val.font = font or bold_font
            c_val.border = thin_border
            c_val.alignment = Alignment(horizontal="center", vertical="center")
            if fill:
                c_val.fill = fill

            curr_row += 1

        ws_summary.column_dimensions["B"].width = 40
        ws_summary.column_dimensions["C"].width = 22

        # Save to buffer
        output_buffer = io.BytesIO()
        wb.save(output_buffer)
        output_buffer.seek(0)
        return output_buffer.getvalue()
