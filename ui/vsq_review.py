import streamlit as st
import pandas as pd
from ui.components import render_header, render_footer, render_back_button, render_confidence_badge, render_status_badge

def highlight_citations(text: str) -> str:
    import re
    # Wrap [Source: ...] in a styled span
    return re.sub(r'(\[Source:.*?\])', r'<span class="citation-highlight">\1</span>', text)

def render():
    render_header()
    st.markdown("### Module Hub → VSQ Engine → Review")
    render_back_button("← Back to Processing", "vsq_processing")
    
    questions = st.session_state.get("questions", [])
    approved_answers = st.session_state.get("approved_answers", {})
    
    if not questions or not approved_answers:
        st.warning("No answers to review.")
        return

    # Filters
    st.markdown("#### Filters")
    f_col1, f_col2, f_col3 = st.columns(3)
    
    with f_col1:
        status_filter = st.selectbox("Status", ["All", "AUTO_APPROVED", "PENDING_REVIEW"])
    with f_col2:
        domains = sorted(list(set([q.domain for q in questions])))
        domain_filter = st.selectbox("Domain", ["All"] + domains)
    with f_col3:
        conf_range = st.slider("Confidence Range", 0.0, 1.0, (0.0, 1.0), 0.05)

    # Metrics
    total_q = len(questions)
    auto_app = sum(1 for a in approved_answers.values() if a.status == "AUTO_APPROVED")
    needs_rev = sum(1 for a in approved_answers.values() if a.status != "AUTO_APPROVED")
    avg_conf = sum(a.confidence_score for a in approved_answers.values()) / max(1, total_q)
    
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("Total Questions", total_q)
    m_col2.metric("Auto-Approved", auto_app)
    m_col3.metric("Pending Review", needs_rev)
    m_col4.metric("Average Confidence", f"{avg_conf:.2f}")

    # Cards
    st.markdown("#### Review Answers")
    
    if st.button("Approve All AUTO_APPROVED"):
        for q_id, ans in approved_answers.items():
            if ans.status == "AUTO_APPROVED":
                ans.status = "SME_APPROVED"
        st.session_state["approved_answers"] = approved_answers
        st.success("All AUTO_APPROVED answers have been marked as SME_APPROVED.")
        st.rerun()

    for q in questions:
        ans = approved_answers.get(q.id)
        if not ans: continue
        
        # Apply filters
        if status_filter != "All" and ans.status != status_filter: continue
        if domain_filter != "All" and q.domain != domain_filter: continue
        if not (conf_range[0] <= ans.confidence_score <= conf_range[1]): continue
        
        header = f"**{q.id}** | {q.domain} | Confidence: {ans.confidence_score:.2f} | {ans.status}"
        with st.expander(header):
            st.markdown(f"**Original Question:**\\n> {q.original_text}")
            
            st.markdown("**Generated Answer:**")
            st.markdown(highlight_citations(ans.final_answer), unsafe_allow_html=True)
            
            st.markdown("**Citations:**")
            cites_data = [{"Source Document": c.source_document, "Section": c.section, "Verbatim Quote": c.quote} for c in ans.citations]
            if cites_data:
                st.dataframe(pd.DataFrame(cites_data), use_container_width=True)
            else:
                st.write("No citations.")
                
            st.markdown(f"*Reasoning: {st.session_state.get('drafted_answers', {}).get(q.id).reasoning if q.id in st.session_state.get('drafted_answers', {}) else ''}*")
            
            b_col1, b_col2, b_col3 = st.columns([1, 1, 3])
            with b_col1:
                if st.button("✅ Approve", key=f"app_{q.id}"):
                    ans.status = "SME_APPROVED"
                    st.session_state["approved_answers"][q.id] = ans
                    st.rerun()
            with b_col2:
                if st.button("🚩 Flag", key=f"flag_{q.id}"):
                    st.toast(f"Flagged Q-{q.id} for SME review.")
            
    if st.button("Proceed to Export →", type="primary"):
        st.session_state["current_page"] = "vsq_export"
        st.rerun()
        
    render_footer()
