"""Custom CSS styles for the modern SaaS dashboard interface."""

CUSTOM_CSS = """
<style>
/* Modern Font & Layout Reset */
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* App Header Styling */
.main-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    padding: 1.75rem 2rem;
    border-radius: 16px;
    margin-bottom: 2rem;
    color: #FFFFFF;
    box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25), 0 8px 10px -6px rgba(15, 23, 42, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.08);
}

.main-header h1 {
    color: #F8FAFC !important;
    font-size: 2.1rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    padding: 0 !important;
    letter-spacing: -0.025em;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.main-header p {
    color: #94A3B8 !important;
    font-size: 0.975rem !important;
    margin: 0.5rem 0 0 0 !important;
    font-weight: 400;
}

.header-badge {
    background: rgba(56, 189, 248, 0.15);
    color: #38BDF8;
    border: 1px solid rgba(56, 189, 248, 0.3);
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: inline-block;
    margin-bottom: 0.5rem;
}

/* Section Cards */
.saas-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.5rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
    margin-bottom: 1.5rem;
}

.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1E293B;
    margin-bottom: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.section-subtitle {
    font-size: 0.85rem;
    color: #64748B;
    margin-bottom: 1.25rem;
}

/* Metric / KPI Cards */
.kpi-container {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1.25rem;
    margin-bottom: 2rem;
}

@media (max-width: 900px) {
    .kpi-container {
        grid-template-columns: repeat(2, 1fr);
    }
}

@media (max-width: 600px) {
    .kpi-container {
        grid-template-columns: 1fr;
    }
}

.kpi-card {
    background: #FFFFFF;
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    border: 1px solid #E2E8F0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.04);
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
}

.kpi-card.blue::before { background: #3B82F6; }
.kpi-card.green::before { background: #10B981; }
.kpi-card.red::before { background: #EF4444; }
.kpi-card.amber::before { background: #F59E0B; }

.kpi-label {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #64748B;
    margin-bottom: 0.35rem;
}

.kpi-value {
    font-size: 1.85rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.1;
}

.kpi-subtext {
    font-size: 0.775rem;
    color: #94A3B8;
    margin-top: 0.4rem;
}

/* Status Badges */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 0.35rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.025em;
}

.badge-green {
    background-color: #ECFDF5;
    color: #047857;
    border: 1px solid #A7F3D0;
}

.badge-red {
    background-color: #FEF2F2;
    color: #B91C1C;
    border: 1px solid #FECACA;
}

.badge-amber {
    background-color: #FFFBEB;
    color: #B45309;
    border: 1px solid #FDE68A;
}

.badge-blue {
    background-color: #EFF6FF;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
}

/* Security Notice Box */
.security-notice {
    background: #F8FAFC;
    border-left: 4px solid #3B82F6;
    padding: 0.75rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: 0.825rem;
    color: #475569;
    margin-top: 0.75rem;
}

/* Real-time Progress Card */
.progress-container {
    background: #F8FAFC;
    border: 1px solid #E2E8F0;
    border-radius: 12px;
    padding: 1rem 1.25rem;
    margin: 1rem 0;
}

/* Dataframe Clean Spacing */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden;
    border: 1px solid #E2E8F0 !important;
}

/* Adjust Streamlit Button Styles */
div.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.65rem 1.5rem !important;
    box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.25) !important;
    transition: all 0.2s ease !important;
}

div.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 12px -2px rgba(37, 99, 235, 0.4) !important;
    transform: translateY(-1px);
}

div.stDownloadButton > button {
    background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.75rem 1.75rem !important;
    box-shadow: 0 4px 6px -1px rgba(5, 150, 105, 0.25) !important;
}

div.stDownloadButton > button:hover {
    box-shadow: 0 6px 12px -2px rgba(5, 150, 105, 0.4) !important;
    transform: translateY(-1px);
}
</style>
"""


def render_header(title: str, subtitle: str, badge: str = "Harness CI/CD Migration Phase 1") -> str:
    """Generate HTML for the top SaaS header banner.

    Args:
        title: App title.
        subtitle: App subtitle.
        badge: Header tag text.

    Returns:
        HTML string.
    """
    return f"""
    <div class="main-header">
        <div class="header-badge">{badge}</div>
        <h1>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"></path>
            </svg>
            {title}
        </h1>
        <p>{subtitle}</p>
    </div>
    """


def render_kpi_cards(
    total: int, accessible: int, not_accessible: int, errors: int, success_rate: str
) -> str:
    """Render modern 4-grid KPI summary metric cards.

    Args:
        total: Total repos evaluated.
        accessible: Count of accessible repos.
        not_accessible: Count of inaccessible repos.
        errors: Count of validation errors.
        success_rate: Formatted success rate percentage.

    Returns:
        HTML string.
    """
    return f"""
    <div class="kpi-container">
        <div class="kpi-card blue">
            <div class="kpi-label">Total Repositories</div>
            <div class="kpi-value">{total}</div>
            <div class="kpi-subtext">Processed from Excel</div>
        </div>
        <div class="kpi-card green">
            <div class="kpi-label">Able to Access</div>
            <div class="kpi-value">{accessible}</div>
            <div class="kpi-subtext">HTTP 200 • Ready ({success_rate})</div>
        </div>
        <div class="kpi-card red">
            <div class="kpi-label">Not Accessible</div>
            <div class="kpi-value">{not_accessible}</div>
            <div class="kpi-subtext">HTTP 404 / 403 • Permission denied</div>
        </div>
        <div class="kpi-card amber">
            <div class="kpi-label">Validation Errors</div>
            <div class="kpi-value">{errors}</div>
            <div class="kpi-subtext">Invalid URL / Rate limited / Timeout</div>
        </div>
    </div>
    """
