import streamlit as st
import os
import tempfile
import chromadb
from config import CHROMA_PERSIST_DIR, CHROMA_COLLECTION
from ui.components import render_header, render_footer, render_back_button
from agents.intake_agent import intake_node

def get_kb_stats():
    try:
        client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        collection = client.get_collection(name=CHROMA_COLLECTION)
        return collection.count()
    except Exception:
        return 0

def render():
    render_header()
    st.markdown("### Module Hub → VSQ Engine → Upload")
    render_back_button("← Back to Module Hub", "module_hub")
    
    with st.sidebar:
        st.markdown("### 📚 Knowledge Base Status")
        chunk_count = get_kb_stats()
        # Mocking the 7 policies indexed for demo purposes
        st.info(f"7 policies indexed\\n\\n{chunk_count} chunks available")

    st.markdown("#### Upload your questionnaire")
    uploaded_file = st.file_uploader("Choose a file", type=["xlsx", "csv", "pdf", "docx"])
    
    if uploaded_file is not None:
        if "file_processed" not in st.session_state or st.session_state.get("last_uploaded_name") != uploaded_file.name:
            file_extension = uploaded_file.name.split(".")[-1].lower()
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name
            
            st.session_state["file_path"] = tmp_path
            st.session_state["file_name"] = uploaded_file.name
            st.session_state["file_type"] = file_extension
            st.session_state["last_uploaded_name"] = uploaded_file.name
            
            with st.spinner("Extracting questions..."):
                state = {
                    "file_path": tmp_path,
                    "file_name": uploaded_file.name,
                    "file_type": file_extension,
                    "questions": [],
                    "processing_log": [],
                    "framework_detected": "Unknown"
                }
                result = intake_node(state)
                st.session_state["questions"] = result["questions"]
                st.session_state["framework_detected"] = result["framework_detected"]
                st.session_state["intake_log"] = result["processing_log"]
                st.session_state["file_processed"] = True
                
        framework = st.session_state.get("framework_detected", "Unknown")
        questions = st.session_state.get("questions", [])
        
        st.success(f"Framework detected: **{framework}**")
        st.metric("Questions Extracted", len(questions))
        
        if questions:
            import pandas as pd
            df = pd.DataFrame([{
                "ID": q.id,
                "Question": q.original_text,
                "Domain": q.domain,
                "Section": q.section,
                "Requires Evidence": q.requires_evidence
            } for q in questions])
            st.dataframe(df, use_container_width=True)
            
            if st.button("Begin Processing →", type="primary"):
                st.session_state["current_page"] = "vsq_processing"
                st.rerun()

    render_footer()
