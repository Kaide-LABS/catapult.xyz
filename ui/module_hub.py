import streamlit as st
from ui.components import render_header, render_footer

def render():
    render_header()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="module-card">
            <div style="font-size: 2rem;">🛡️</div>
            <div><span class="badge badge-ready">Architecture Ready</span></div>
            <div class="card-title">Virtual FDE Data Sanitation Pipeline</div>
            <div class="card-desc">Autonomous PII redaction, dynamic RBAC mapping, and vector lifecycle management. Ensures your RAG pipeline ingests only pristine, compliant data.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Architecture →", key="btn_fde", use_container_width=True):
            st.session_state["current_page"] = "arch_fde"
            st.rerun()

    with col2:
        st.markdown("""
        <div class="module-card">
            <div style="font-size: 2rem;">⚡</div>
            <div><span class="badge badge-ready">Architecture Ready</span></div>
            <div class="card-title">Kinetic Action Dispatcher</div>
            <div class="card-desc">Translates AI-generated insights into deterministic API calls across enterprise systems. HITL validation gates ensure safe kinetic execution.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("View Architecture →", key="btn_kinetic", use_container_width=True):
            st.session_state["current_page"] = "arch_kinetic"
            st.rerun()

    with col3:
        st.markdown("""
        <div class="module-card live-card">
            <div style="font-size: 2rem;">✅</div>
            <div><span class="badge badge-live">Live Demo</span></div>
            <div class="card-title">VSQ Compliance Engine</div>
            <div class="card-desc">Multi-agent system that autonomously ingests, answers, and routes vendor security questionnaires with deterministic citation enforcement.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Launch Demo →", key="btn_vsq", use_container_width=True, type="primary"):
            st.session_state["current_page"] = "vsq_upload"
            st.rerun()
            
    render_footer()
