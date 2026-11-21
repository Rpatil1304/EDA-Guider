import streamlit as st

from api import analyze_dataset
from components.report import display_report
from components.clean_section import display_clean_section


st.set_page_config(
    page_title="EDA-Guider",
    page_icon="📊",
    layout="wide",
)

st.title("EDA-Guider")

# Initialize UI mode in session state
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "RAW"

# 2 Selection Buttons on UI: "RAW" and "Clean"
st.write("Select the workflow for your dataset:")
col1, col2 = st.columns(2)

with col1:
    raw_active = st.session_state["app_mode"] == "RAW"
    if st.button(
        "📁 RAW Dataset (Automated EDA)",
        use_container_width=True,
        type="primary" if raw_active else "secondary",
        key="btn_mode_raw",
    ):
        st.session_state["app_mode"] = "RAW"
        st.rerun()

with col2:
    clean_active = st.session_state["app_mode"] == "Clean"
    if st.button(
        "🧹 Clean Dataset (AI Q&A & Visualizer)",
        use_container_width=True,
        type="primary" if clean_active else "secondary",
        key="btn_mode_clean",
    ):
        st.session_state["app_mode"] = "Clean"
        st.rerun()

st.markdown("---")

# ============================================================
# Mode 1: RAW Dataset (Existing EDA Pipeline)
# ============================================================
if st.session_state["app_mode"] == "RAW":
    st.subheader("📁 RAW Dataset: Automated EDA Report")
    st.write(
        "Upload your raw dataset to profile it, generate rule-based preprocessing plans, "
        "and produce comprehensive EDA reports."
    )

    uploaded_file = st.file_uploader(
        "Upload your raw dataset",
        type=[
            "csv",
            "tsv",
            "xlsx",
            "xls",
            "xlsm",
        ],
        key="raw_dataset_uploader",
    )

    if "raw_eda_result" not in st.session_state:
        st.session_state["raw_eda_result"] = None
    if "raw_file_id" not in st.session_state:
        st.session_state["raw_file_id"] = None

    if uploaded_file is not None:
        file_id = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state.get("raw_file_id") != file_id:
            st.session_state["raw_eda_result"] = None
            st.session_state["raw_file_id"] = file_id

        st.success(f"File selected: {uploaded_file.name}")

        if st.button(
            "Generate EDA Report",
            type="primary",
            key="btn_generate_raw_eda",
        ):
            with st.spinner("Analyzing your dataset and generating EDA report..."):
                try:
                    result = analyze_dataset(uploaded_file)

                    if result.get("status") != "success":
                        st.error("EDA analysis failed.")
                    else:
                        st.session_state["raw_eda_result"] = result

                except Exception as error:
                    st.error(
                        "Failed to communicate with the EDA backend."
                    )
                    st.exception(error)

        if st.session_state.get("raw_eda_result") is not None:
            st.success("EDA report generated successfully.")
            display_report(st.session_state["raw_eda_result"])

# ============================================================
# Mode 2: Clean Dataset (AI Q&A & Visualization Assistant)
# ============================================================
else:
    display_clean_section()
