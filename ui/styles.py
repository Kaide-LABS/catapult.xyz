import streamlit as st

def inject_styles():
    css = """
    <style>
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Base font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
    }

    /* Cards */
    .module-card {
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 24px;
        height: 320px;
        background-color: #0f172a;
        transition: transform 0.2s, box-shadow 0.2s;
        display: flex;
        flex-direction: column;
    }
    .module-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.5);
    }
    .module-card.live-card {
        border-color: #22c55e;
        box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.2);
    }
    .card-title {
        font-size: 1.25rem;
        font-weight: 600;
        margin-top: 16px;
        margin-bottom: 8px;
        color: #f8fafc;
    }
    .card-desc {
        color: #94a3b8;
        flex-grow: 1;
        font-size: 0.95rem;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .badge-ready {
        background-color: #64748b;
        color: white;
    }
    .badge-live {
        background-color: #22c55e;
        color: white;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); }
        100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    .badge-confidence-high { background-color: #22c55e; color: white; }
    .badge-confidence-medium { background-color: #f59e0b; color: white; }
    .badge-confidence-low { background-color: #ef4444; color: white; }
    
    .badge-status-approved { background-color: #22c55e; color: white; }
    .badge-status-pending { background-color: #f59e0b; color: white; }

    /* Processing Feed */
    .log-container {
        background-color: #1e1e2e;
        border-radius: 8px;
        padding: 16px;
        max-height: 400px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
        font-size: 0.85rem;
        border: 1px solid #334155;
    }
    .log-entry { margin-bottom: 4px; }
    .log-intake { color: #60a5fa; }
    .log-retrieval { color: #c084fc; }
    .log-drafting { color: #fb923c; }
    .log-routing-high { color: #4ade80; }
    .log-routing-low { color: #fbbf24; }
    .log-export { color: #f8fafc; }
    .log-default { color: #94a3b8; }
    
    .citation-highlight {
        background-color: rgba(96, 165, 250, 0.2);
        padding: 0 4px;
        border-radius: 4px;
        font-size: 0.9em;
        color: #93c5fd;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
