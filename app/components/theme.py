"""UI Theme, Custom CSS, and color palettes for GIGLEDGER dashboard."""

PRIMARY_COLOR = "#0F172A"       # Deep Slate
ACCENT_GREEN = "#10B981"        # Emerald (Net Earnings)
ACCENT_BLUE = "#3B82F6"         # Sapphire (Gross Earnings)
ACCENT_RED = "#EF4444"          # Coral Red (Expenses / Deductions)
ACCENT_AMBER = "#F59E0B"        # Amber (Incentives & Warnings)
ACCENT_PURPLE = "#8B5CF6"       # Violet (Time / Hours)

CUSTOM_CSS = """
<style>
    /* Global Typography & Spacing */
    .main {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Metric Card Styling */
    .metric-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02));
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #94A3B8;
        margin-bottom: 6px;
        font-weight: 600;
    }
    
    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        line-height: 1.2;
    }
    
    .metric-subtext {
        font-size: 0.8rem;
        color: #64748B;
        margin-top: 4px;
    }
    
    /* Disclaimer Badges */
    .badge-demo {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #FCD34D;
    }
    
    .badge-research {
        background-color: #DBEAFE;
        color: #1E40AF;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #93C5FD;
    }
    
    .badge-participant {
        background-color: #D1FAE5;
        color: #065F46;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        border: 1px solid #6EE7B7;
    }
</style>
"""


def apply_theme():
    """Inject custom CSS into Streamlit page."""
    import streamlit as st
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
