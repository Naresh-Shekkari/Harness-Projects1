"""Script to generate a sample Excel spreadsheet for testing the application."""

from pathlib import Path
import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter


def create_sample_file(output_path: str = "sample_repositories.xlsx"):
    """Create a sample repositories Excel workbook with realistic data."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Repositories"
    ws.views.sheetView[0].showGridLines = True

    # Styling
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="Segoe UI", size=10)
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    headers = [
        "Repository Name",
        "GitHub URL",
        "Business Unit",
        "Lead Developer",
        "Jenkins Job Name",
    ]

    for col_idx, header in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border
    ws.row_dimensions[1].height = 28

    sample_data = [
        (
            "payment-service",
            "https://github.com/octocat/Hello-World",
            "Core Banking",
            "Alice Chen",
            "PROD-payment-service-build",
        ),
        (
            "customer-api",
            "https://github.com/octocat/Spoon-Knife",
            "Retail Banking",
            "Bob Smith",
            "PROD-customer-api-deploy",
        ),
        (
            "order-management",
            "https://github.com/psf/requests",
            "E-Commerce",
            "Carol Davis",
            "PROD-order-mgmt-pipeline",
        ),
        (
            "notification-service",
            "https://github.com/pallets/flask",
            "Infrastructure",
            "David Wilson",
            "INFRA-notification-svc",
        ),
        (
            "employee-portal",
            "https://github.com/company/employee-portal",
            "Internal Tools",
            "Eva Green",
            "INTERNAL-employee-portal",
        ),
        (
            "legacy-crm-bridge",
            "https://github.com/nonexistent-org-2026/does-not-exist-repo",
            "Enterprise CRM",
            "Frank Miller",
            "LEGACY-crm-bridge-sync",
        ),
        (
            "malformed-url-app",
            "invalid-url-without-protocol-or-domain",
            "DevOps Test",
            "Grace Hopper",
            "TEST-bad-url-pipeline",
        ),
    ]

    for row_idx, row_data in enumerate(sample_data, start=2):
        ws.row_dimensions[row_idx].height = 22
        for col_idx, value in enumerate(row_data, start=1):
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(vertical="center")

    # Set column widths
    for col in ws.columns:
        max_len = max(len(str(cell.value or "")) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 16)

    target_path = Path(output_path).resolve()
    wb.save(target_path)
    print(f"Sample Excel created successfully at: {target_path}")


if __name__ == "__main__":
    create_sample_file()
