import streamlit as st

def render_header():
    st.title("Scatterbot Agentic Sidecar Suite")
    st.caption("Enterprise deployment infrastructure for AI workspaces")
    st.markdown("---")

def render_footer():
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #64748b; font-size: 0.8rem;'>Architected for Catapult by Scatterbot</p>", unsafe_allow_html=True)

def render_back_button(label: str, target_page: str):
    if st.button(label):
        st.session_state["current_page"] = target_page
        st.rerun()

def render_confidence_badge(score: float) -> str:
    if score >= 0.95:
        return f'<span class="badge badge-confidence-high">Confidence: {score:.2f}</span>'
    elif score >= 0.80:
        return f'<span class="badge badge-confidence-medium">Confidence: {score:.2f}</span>'
    else:
        return f'<span class="badge badge-confidence-low">Confidence: {score:.2f}</span>'

def render_status_badge(status: str) -> str:
    if status == "AUTO_APPROVED" or status == "SME_APPROVED":
        return f'<span class="badge badge-status-approved">{status}</span>'
    else:
        return f'<span class="badge badge-status-pending">{status}</span>'
