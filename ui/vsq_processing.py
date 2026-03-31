import streamlit as st
import time
from ui.components import render_header, render_footer
from agents.retrieval_agent import perform_retrieval
from agents.drafting_agent import perform_drafting
from agents.routing_agent import perform_routing
from agents.export_agent import export_node

def render():
    render_header()
    st.markdown("### Module Hub → VSQ Engine → Processing")
    
    if "questions" not in st.session_state or not st.session_state["questions"]:
        st.warning("No questions to process. Please go back and upload a file.")
        if st.button("← Back to Upload"):
            st.session_state["current_page"] = "vsq_upload"
            st.rerun()
        return

    questions = st.session_state["questions"]
    total = len(questions)
    
    # Initialize state
    if "processing_started" not in st.session_state:
        st.session_state["processing_started"] = True
        st.session_state["completed_count"] = 0
        st.session_state["retrieval_results"] = {}
        st.session_state["drafted_answers"] = {}
        st.session_state["approved_answers"] = {}
        st.session_state["processing_log"] = st.session_state.get("intake_log", [])
        st.session_state["auto_approved"] = 0
        st.session_state["needs_review"] = 0
        st.session_state["total_confidence"] = 0.0
        st.session_state["processing_complete"] = False

    col1, col2 = st.columns([0.7, 0.3])
    
    with col2:
        st.markdown("#### Live Statistics")
        metric_auto = st.empty()
        metric_review = st.empty()
        metric_conf = st.empty()
        metric_prog = st.empty()
        
        def update_metrics():
            metric_auto.metric("Auto-Approved", st.session_state["auto_approved"])
            metric_review.metric("Needs Review", st.session_state["needs_review"])
            avg_conf = st.session_state["total_confidence"] / max(1, st.session_state["completed_count"])
            metric_conf.metric("Average Confidence", f"{avg_conf:.2f}")
            metric_prog.metric("Questions Processed", f'{st.session_state["completed_count"]}/{total}')
            
        update_metrics()

    with col1:
        st.markdown("#### Activity Feed")
        progress_bar = st.progress(st.session_state["completed_count"] / max(1, total))
        log_container = st.empty()
        
        def render_logs():
            html = '<div class="log-container">'
            for entry in st.session_state["processing_log"]:
                cls = "log-default"
                if "[Intake]" in entry: cls = "log-intake"
                elif "[Retrieval]" in entry: cls = "log-retrieval"
                elif "[Drafting]" in entry: cls = "log-drafting"
                elif "[Routing]" in entry:
                    cls = "log-routing-high" if "AUTO_APPROVED" in entry else "log-routing-low"
                elif "[Export]" in entry: cls = "log-export"
                elif "[Process]" in entry:
                    cls = "log-routing-high" if "AUTO_APPROVED" in entry else "log-routing-low"
                
                html += f'<div class="log-entry {cls}">{entry}</div>'
            html += '</div>'
            log_container.markdown(html, unsafe_allow_html=True)
            
        render_logs()
        
        if not st.session_state["processing_complete"]:
            for i, q in enumerate(questions):
                if q.id in st.session_state["approved_answers"]:
                    continue
                
                # 1. Retrieval
                retrieval_res = perform_retrieval(q)
                st.session_state["retrieval_results"][q.id] = retrieval_res
                st.session_state["processing_log"].append(f"[Retrieval] Q-{q.id}: found {len(retrieval_res.chunks)} chunks, confidence={retrieval_res.retrieval_confidence:.2f}")
                render_logs()
                
                # 2. Drafting
                draft_res = perform_drafting(q, retrieval_res)
                st.session_state["drafted_answers"][q.id] = draft_res
                st.session_state["processing_log"].append(f"[Drafting] Q-{q.id}: generated answer, conf={draft_res.confidence_score:.2f}")
                render_logs()
                
                # 3. Routing
                approved_res = perform_routing(draft_res)
                st.session_state["approved_answers"][q.id] = approved_res
                st.session_state["processing_log"].append(f"[Process] Q-{q.id}: routed as {approved_res.status}")
                
                st.session_state["completed_count"] += 1
                st.session_state["total_confidence"] += approved_res.confidence_score
                if approved_res.status == "AUTO_APPROVED":
                    st.session_state["auto_approved"] += 1
                else:
                    st.session_state["needs_review"] += 1
                
                progress_bar.progress(st.session_state["completed_count"] / total)
                update_metrics()
                render_logs()
                
            # Export
            export_state = {
                "file_path": st.session_state["file_path"],
                "file_type": st.session_state["file_type"],
                "questions": st.session_state["questions"],
                "approved_answers": st.session_state["approved_answers"]
            }
            export_res = export_node(export_state)
            st.session_state["export_path"] = export_res["export_path"]
            st.session_state["processing_log"].extend(export_res["processing_log"])
            
            st.session_state["processing_complete"] = True
            render_logs()
            st.rerun()

    if st.session_state.get("processing_complete"):
        st.success(f"Processing complete! All {total} questions answered.")
        if st.button("Review Answers →", type="primary"):
            st.session_state["current_page"] = "vsq_review"
            st.rerun()

    render_footer()
