"""Unit tests for Excel loading, validation, and report generation."""

import io
import openpyxl
import pandas as pd
import pytest

from config.settings import (
    AccessStatus,
    COL_ACCESS_STATUS,
    COL_HTTP_STATUS,
    COL_VALIDATION_MESSAGE,
)
from services.excel_service import ExcelService, ExcelValidationError


def test_load_and_validate_standard_columns():
    """Test loading Excel with standard column names."""
    df_raw = pd.DataFrame({
        "Repository Name": ["payment-service", "customer-api"],
        "GitHub URL": [
            "https://github.com/company/payment-service",
            "https://github.com/company/customer-api",
        ],
    })
    buf = io.BytesIO()
    df_raw.to_excel(buf, index=False)

    df_loaded, repo_col, url_col = ExcelService.load_and_validate_input(buf.getvalue())

    assert len(df_loaded) == 2
    assert repo_col == "Repository Name"
    assert url_col == "GitHub URL"


def test_load_and_validate_column_variations():
    """Test loading Excel with column synonyms (e.g. Repo Name, Git URL)."""
    df_raw = pd.DataFrame({
        "Repo Name": ["order-svc"],
        "Git URL": ["https://github.com/org/order-svc"],
        "Business Unit": ["Finance"],
    })
    buf = io.BytesIO()
    df_raw.to_excel(buf, index=False)

    df_loaded, repo_col, url_col = ExcelService.load_and_validate_input(buf.getvalue())

    assert len(df_loaded) == 1
    assert repo_col == "Repo Name"
    assert url_col == "Git URL"
    assert "Business Unit" in df_loaded.columns


def test_load_and_validate_missing_columns():
    """Test exception raised when required columns are absent."""
    df_bad = pd.DataFrame({
        "Application": ["svc1"],
        "Notes": ["Some notes"],
    })
    buf = io.BytesIO()
    df_bad.to_excel(buf, index=False)

    with pytest.raises(ExcelValidationError) as exc_info:
        ExcelService.load_and_validate_input(buf.getvalue())

    assert "Missing required column" in str(exc_info.value)


def test_load_and_validate_empty_file():
    """Test handling of empty excel file."""
    df_empty = pd.DataFrame()
    buf = io.BytesIO()
    df_empty.to_excel(buf, index=False)

    with pytest.raises(ExcelValidationError):
        ExcelService.load_and_validate_input(buf.getvalue())


def test_generate_excel_report_structure_and_styling():
    """Test generation of styled output workbook with both sheets and accurate cells."""
    results_df = pd.DataFrame({
        "Repository Name": ["app1", "app2", "app3"],
        "GitHub URL": [
            "https://github.com/company/app1",
            "https://github.com/company/app2",
            "https://github.com/company/app3",
        ],
        "Extra Column": ["data1", "data2", "data3"],
        COL_ACCESS_STATUS: [
            AccessStatus.ABLE_TO_ACCESS.value,
            AccessStatus.NOT_ACCESSIBLE.value,
            AccessStatus.VALIDATION_ERROR.value,
        ],
        COL_HTTP_STATUS: ["200", "404", "N/A"],
        COL_VALIDATION_MESSAGE: [
            "Repository is accessible.",
            "Repository not found or inaccessible.",
            "Invalid GitHub URL format.",
        ],
    })

    excel_bytes = ExcelService.generate_excel_report(results_df)
    assert isinstance(excel_bytes, bytes)
    assert len(excel_bytes) > 0

    # Parse back the generated workbook to verify contents
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes))

    # Verify both sheets exist
    assert "Validation Results" in wb.sheetnames
    assert "Executive Summary" in wb.sheetnames

    # Check Validation Results sheet
    ws_results = wb["Validation Results"]
    assert ws_results.cell(row=1, column=1).value == "Repository Name"
    assert ws_results.cell(row=1, column=4).value == COL_ACCESS_STATUS

    # Check row data values
    assert ws_results.cell(row=2, column=4).value == AccessStatus.ABLE_TO_ACCESS.value
    assert ws_results.cell(row=3, column=4).value == AccessStatus.NOT_ACCESSIBLE.value
    assert ws_results.cell(row=4, column=4).value == AccessStatus.VALIDATION_ERROR.value

    # Check Executive Summary sheet
    ws_summary = wb["Executive Summary"]
    summary_text = [
        str(cell.value)
        for row in ws_summary.iter_rows()
        for cell in row
        if cell.value is not None
    ]
    assert any("GitHub Repository Access Validation Summary" in t for t in summary_text)
    assert any("Total Repositories Evaluated" in t for t in summary_text)
