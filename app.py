import streamlit as st
from ui.styles import inject_styles

st.set_page_config(page_title="Scatterbot Sidecar Suite", page_icon="🚀", layout="wide")
inject_styles()

if "current_page" not in st.session_state:
    st.session_state["current_page"] = "module_hub"

page = st.session_state["current_page"]

if page == "module_hub":
    from ui.module_hub import render
    render()
elif page == "vsq_upload":
    from ui.vsq_upload import render
    render()
elif page == "vsq_processing":
    from ui.vsq_processing import render
    render()
elif page == "vsq_review":
    from ui.vsq_review import render
    render()
elif page == "vsq_export":
    from ui.vsq_export import render
    render()
elif page == "arch_fde":
    from ui.architecture_fde import render
    render()
elif page == "arch_kinetic":
    from ui.architecture_kinetic import render
    render()
