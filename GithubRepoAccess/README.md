# GitHub Repository Access Validator (Phase 1)

> **Automating repository access verification for enterprise Jenkins-to-Harness CI/CD migrations.**

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B.svg)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/tests-21%20passed-brightgreen.svg)]()
[![Code Style](https://img.shields.io/badge/code%20style-PEP%208-black.svg)]()

---

## 1. Project Overview

As part of migrating thousands of enterprise application repositories from legacy **Jenkins** infrastructure to **Harness CI/CD**, migration engineers receive repository inventories through Excel spreadsheets provided by distributed application teams.

Historically, verifying whether the migration team's automation credentials could access each repository required manual copy-pasting, opening URLs in browsers, and manually marking spreadsheets.

**GitHub Repository Access Validator** automates this entire validation workflow:
- Ingests application team Excel files (`.xlsx` and `.xls`).
- Authenticates securely with a GitHub Personal Access Token (PAT).
- Validates repository accessibility through the official GitHub REST API.
- Visualizes results in a modern SaaS administration dashboard.
- Exports a styled, color-coded executive Excel report preserving all original columns.

---

## 2. Business Use Case

```
[Application Teams] 
       │ (Excel inventory with repo URLs)
       ▼
[GitHub Repo Access Validator]
       │
       ├─► Validates GitHub PAT (server-memory only)
       ├─► Calls GitHub REST API (GET /repos/{owner}/{repo})
       │      ├─► 200: ABLE TO ACCESS (Migration Ready)
       │      ├─► 404: NOT ACCESSIBLE (Private / Not Found / Lacks Access)
       │      ├─► 403: NOT ACCESSIBLE (Permission Denied)
       │      ├─► 401: AUTH FAILED (Halts immediately to protect data)
       │      └─► 429/Timeout: VALIDATION ERROR
       │
       ▼
[Executive Excel Report + Modern Dashboard]
       │
       └─► Ready for Harness pipeline onboarding
```

---

## 3. Architecture & Design Principles

The application is structured into decoupled, modular layers:

```
┌─────────────────────────────────────────────────────────────┐
│                       Streamlit UI                          │
│          (app.py, ui/dashboard.py, ui/styles.py)            │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 Validation Orchestration                    │
│            (services/validation_service.py)                 │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│      GitHub REST Client     │ │        Excel Engine         │
│ (services/github_service.py)│ │ (services/excel_service.py) │
│  - Token Authentication     │ │  - Column Name Aliases      │
│  - Access Verification      │ │  - OpenPyXL Styler          │
│  - Rate-limit handling      │ │  - Multi-sheet Executive Rpt│
└──────────────┬──────────────┘ └──────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────┐ ┌─────────────────────────────┐
│     Security & Logging      │ │    URL & Column Parsers     │
│      (utils/logger.py)      │ │    (utils/validators.py)    │
│  - Sensitive Token Scrubber │ │  - Regex URL Extraction     │
│  - Safe Terminal Output     │ │  - Owner/Repo Parsers       │
└─────────────────────────────┘ └─────────────────────────────┘
```

### Security & Token Governance
- **Never Hardcoded:** PAT is strictly inputted via masked password fields.
- **Server-Side Memory Only:** The PAT is held in volatile server memory for the active execution session and discarded.
- **No Token Logging:** Log output runs through `SensitiveDataScrubber` which redacts PAT patterns (`ghp_*`, `github_pat_*`).
- **No File Storage:** Tokens are never written to disk, config files, or exported Excel files.
- **Immediate 401 Abort:** If a PAT expires or is invalid (HTTP 401), the validation halts immediately rather than incorrectly marking hundreds of repositories as inaccessible.

---

## 4. Technology Stack

- **Backend:** Python 3.10+
- **API Client:** Requests 2.31+ (GitHub REST API v2022-11-28)
- **Frontend / Dashboard:** Streamlit 1.32+ with custom SaaS CSS
- **Spreadsheet Processing:** Pandas 2.2+, OpenPyXL 3.1+
- **Unit Testing:** Pytest 8.0+, unittest.mock

---

## 5. Project Folder Structure

```
GithubRepoAccess/
├── app.py                      # Main Streamlit application entry point
├── create_sample_excel.py      # Utility script generating sample Excel data
├── requirements.txt            # Project dependencies
├── sample_repositories.xlsx    # Sample input Excel for testing
├── README.md                   # Documentation and execution guide
├── .env.example                # Example configuration reference
├── .gitignore                  # Git ignore rules for Python/Streamlit
│
├── config/
│   ├── __init__.py
│   └── settings.py             # Constants, status enums, aliases, styling colors
│
├── services/
│   ├── __init__.py
│   ├── github_service.py       # GitHub REST API client & auth verification
│   ├── excel_service.py        # Excel ingestion, validation & openpyxl report generator
│   └── validation_service.py   # Validation workflow orchestrator & stats calculator
│
├── utils/
│   ├── __init__.py
│   ├── logger.py               # Security-scrubbed logger (redacts tokens)
│   └── validators.py           # GitHub URL regex extractor & column matching
│
├── ui/
│   ├── __init__.py
│   ├── dashboard.py            # Streamlit dashboard layout & interaction controller
│   └── styles.py               # Custom CSS styles, KPI cards & badges
│
├── tests/
│   ├── __init__.py
│   ├── test_github_service.py      # Tests for HTTP 200, 401, 403, 404, 429, timeouts
│   ├── test_excel_service.py       # Tests for column synonyms, missing headers, report generation
│   └── test_validation_service.py  # Tests for batch orchestration & 401 abort
│
└── logs/
    └── .gitkeep
```

---

## 6. Windows 11 PowerShell Setup Guide

Follow these commands in **Windows PowerShell** to configure and run the application.

### Step 1: Open PowerShell in Project Directory
```powershell
Set-Location "C:\Users\Naresh\Documents\GitHub\Harness-Projects\GithubRepoAccess"
```

### Step 2: Verify Python 3 Installation
```powershell
python --version
```
*(Ensure Python 3.10 or higher is installed)*

### Step 3: Create a Virtual Environment
```powershell
python -m venv venv
```

### Step 4: Activate the Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```
> *Tip: If PowerShell displays an execution policy error, run:*
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 5: Upgrade Pip & Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 7. GitHub Personal Access Token (PAT) Instructions

### Creating a Token
1. Log in to your GitHub account.
2. Navigate to **Settings** > **Developer settings** > **Personal access tokens**.
3. Choose either:
   - **Fine-grained personal access tokens** (Recommended for enterprise organizations):
     - Resource owner: Choose your Organization.
     - Repository access: *All repositories* or *Selected repositories*.
     - Repository permissions: `Metadata` -> **Read-only**.
   - **Tokens (classic)**:
     - Scopes: Select `repo` (Full control of private repositories) or `read:org`.
4. Generate and copy the token string (starts with `github_pat_` or `ghp_`).

---

## 8. Running the Application

Launch the Streamlit web dashboard:
```powershell
streamlit run app.py
```

The application will launch automatically in your default browser at:
```
http://localhost:8501
```

---

## 9. Running Unit Tests

Execute the comprehensive Pytest test suite (all tests mock GitHub API calls; no token required):
```powershell
python -m pytest -v
```

Expected output:
```
tests/test_excel_service.py .....                                        [ 23%]
tests/test_github_service.py ............                                [ 80%]
tests/test_validation_service.py ....                                    [100%]
============================= 21 passed in 0.61s ==============================
```

---

## 10. Sample Excel Input & Testing Instructions

A ready-to-use sample spreadsheet `sample_repositories.xlsx` is provided in the repository root.

### Generating / Refreshing the Sample File
```powershell
python create_sample_excel.py
```

### Sample Input Structure
| Repository Name | GitHub URL | Business Unit | Lead Developer | Jenkins Job Name |
| :--- | :--- | :--- | :--- | :--- |
| payment-service | `https://github.com/octocat/Hello-World` | Core Banking | Alice Chen | PROD-payment-service-build |
| customer-api | `https://github.com/octocat/Spoon-Knife` | Retail Banking | Bob Smith | PROD-customer-api-deploy |
| order-management | `https://github.com/psf/requests` | E-Commerce | Carol Davis | PROD-order-mgmt-pipeline |
| notification-service | `https://github.com/pallets/flask` | Infrastructure | David Wilson | INFRA-notification-svc |
| employee-portal | `https://github.com/company/employee-portal` | Internal Tools | Eva Green | INTERNAL-employee-portal |
| legacy-crm-bridge | `https://github.com/nonexistent-org-2026/does-not-exist` | Enterprise CRM | Frank Miller | LEGACY-crm-bridge-sync |
| malformed-url-app | `invalid-url-without-domain` | DevOps Test | Grace Hopper | TEST-bad-url-pipeline |

### Column Name Flexibility
The application automatically recognizes common synonyms:
- **Repository Name Column:** `Repository Name`, `Repo Name`, `Repository`, `Repo`, `App Name`, `Application Name`
- **GitHub URL Column:** `GitHub URL`, `Repository URL`, `Repo URL`, `Git URL`, `URL`, `GitHub Link`

---

## 11. Expected Excel Output Structure

The generated Excel report preserves all original columns and appends three standardized columns:

| Repository Name | GitHub URL | ...Original Cols... | Access Status | HTTP Status | Validation Message |
| :--- | :--- | :--- | :---: | :---: | :--- |
| payment-service | `https://github.com/...` | ... | **ABLE TO ACCESS** (Green) | 200 | Repository is accessible. |
| employee-portal | `https://github.com/...` | ... | **NOT ACCESSIBLE** (Red) | 404 | Repository not found or inaccessible with the supplied credentials. |
| malformed-url-app | `invalid-url...` | ... | **VALIDATION ERROR** (Orange) | N/A | Invalid GitHub repository URL format. |

### Styling Features
- **Sheet 1 ("Validation Results"):**
  - Dark slate header with white bold text.
  - Soft green highlight (`#D4EDDA`) for `ABLE TO ACCESS`.
  - Soft red highlight (`#F8D7DA`) for `NOT ACCESSIBLE`.
  - Soft amber highlight (`#FFF3CD`) for `VALIDATION ERROR`.
  - Alternating zebra rows for readability.
  - Auto-fitted column widths.
- **Sheet 2 ("Executive Summary"):**
  - Summary metrics card table: Total Repositories, Accessible, Not Accessible, Validation Errors, and Success Rate %.
  - Generation timestamp and migration phase metadata.

---

## 12. Known Limitations (Phase 1 Scope)

In accordance with Phase 1 project boundaries:
1. **Validation Only:** Does not perform Jenkins pipeline parsing or Harness migration.
2. **Sequential Requests:** Repositories are checked sequentially with a 15-second timeout to prevent triggering GitHub API secondary rate limits.
3. **Private 404 Behavior:** GitHub returns HTTP 404 for private repositories when the token lacks permission. This is accurately reported as `NOT ACCESSIBLE` rather than assuming the repository was deleted.
4. **No Direct Clone:** Phase 1 validates metadata API access without downloading git commit trees or cloning repositories.
