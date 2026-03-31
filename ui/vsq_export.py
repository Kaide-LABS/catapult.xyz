import streamlit as st
import os
import json
from ui.components import render_header, render_footer, render_back_button

def render():
    render_header()
    st.markdown("### Module Hub → VSQ Engine → Export")
    render_back_button("← Back to Review", "vsq_review")
    
    export_path = st.session_state.get("export_path", "")
    questions = st.session_state.get("questions", [])
    approved_answers = st.session_state.get("approved_answers", {})
    
    total_q = len(questions)
    auto_app = sum(1 for a in approved_answers.values() if a.status == "AUTO_APPROVED" or a.status == "SME_APPROVED")
    auto_rate = (auto_app / max(1, total_q)) * 100
    avg_conf = sum(a.confidence_score for a in approved_answers.values()) / max(1, total_q)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Questions", total_q)
    col2.metric("Approval Rate", f"{auto_rate:.1f}%")
    col3.metric("Average Confidence", f"{avg_conf:.2f}")
    col4.metric("Estimated Time Saved", f"~{total_q * 10 / 60:.1f} hours → 2 mins")
    
    st.markdown("#### Downloads")
    
    d_col1, d_col2 = st.columns(2)
    
    with d_col1:
        if os.path.exists(export_path):
            with open(export_path, "rb") as f:
                st.download_button(
                    label="📥 Download Completed Questionnaire",
                    data=f.read(),
                    file_name=os.path.basename(export_path),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" if export_path.endswith(".xlsx") else "text/csv",
                    type="primary",
                    use_container_width=True
                )
        else:
            st.error("Export file not found.")
            
    with d_col2:
        audit_data = []
        for q_id, ans in approved_answers.items():
            audit_data.append({
                "question_id": q_id,
                "status": ans.status,
                "confidence": ans.confidence_score,
                "citations": [{"source": c.source_document, "section": c.section, "quote": c.quote} for c in ans.citations]
            })
            
        st.download_button(
            label="📥 Download Audit Trail (JSON)",
            data=json.dumps(audit_data, indent=2),
            file_name="vsq_audit_trail.json",
            mime="application/json",
            use_container_width=True
        )

    st.markdown("---")
    if st.button("Return to Module Hub"):
        st.session_state.clear()
        st.session_state["current_page"] = "module_hub"
        st.rerun()
        
    render_footer()
