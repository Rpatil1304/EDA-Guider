"""Streamlit component for the Clean Dataset Q&A and visualization assistant."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from api import fetch_clean_metadata, submit_clean_query


def display_clean_section():
    """Render the Clean Dataset Q&A assistant in the Streamlit frontend."""
    st.subheader("🧹 Clean Dataset Assistant")
    st.write(
        "Upload a pre-cleaned dataset (CSV or Excel) to extract comprehensive "
        "metadata and ask questions in natural language. The AI will generate "
        "Python code, execute it securely, and provide direct answers with interactive charts."
    )

    clean_file = st.file_uploader(
        "Upload your clean dataset",
        type=["csv", "tsv", "xlsx", "xls", "xlsm"],
        key="clean_dataset_uploader",
    )

    if clean_file is None:
        st.info("Please upload a clean CSV or Excel dataset to begin.")
        # Clear clean state if file removed
        if "clean_metadata" in st.session_state:
            del st.session_state["clean_metadata"]
        if "clean_query_history" in st.session_state:
            del st.session_state["clean_query_history"]
        return

    # Initialize query history in session state
    if "clean_query_history" not in st.session_state:
        st.session_state["clean_query_history"] = []

    # File info indicator
    st.success(f"Loaded Clean File: **{clean_file.name}**")

    # Step 1: Extract or retrieve cached metadata
    file_id = f"{clean_file.name}_{clean_file.size}"
    if (
        "clean_metadata" not in st.session_state
        or st.session_state.get("clean_file_id") != file_id
    ):
        with st.spinner("Extracting dataset profile and metadata..."):
            try:
                res = fetch_clean_metadata(clean_file)
                st.session_state["clean_metadata"] = res.get("metadata", {})
                st.session_state["clean_file_id"] = file_id
                st.session_state["clean_query_history"] = []
            except Exception as e:
                st.error("Failed to extract metadata from backend.")
                st.exception(e)
                return

    metadata: Dict[str, Any] = st.session_state.get("clean_metadata", {})
    summary = metadata.get("summary", {})

    # Display KPI Metrics
    st.markdown("### 📊 Dataset Overview")
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    with kpi_col1:
        st.metric("Total Rows", f"{summary.get('total_rows', 0):,}")
    with kpi_col2:
        st.metric("Total Columns", f"{summary.get('total_columns', 0):,}")
    with kpi_col3:
        st.metric("Missing Cells", f"{summary.get('missing_cell_percentage', 0)}%")
    with kpi_col4:
        st.metric("Duplicate Rows", f"{summary.get('duplicate_rows', 0):,}")

    # Expandable Metadata Inspection
    with st.expander("📋 View Column Details & Data Types"):
        col_groups = metadata.get("column_groups", {})
        sub_c1, sub_c2, sub_c3 = st.columns(3)
        with sub_c1:
            st.markdown(f"**Numeric Columns ({len(col_groups.get('numeric', []))})**")
            st.write(col_groups.get("numeric", []))
        with sub_c2:
            st.markdown(f"**Categorical ({len(col_groups.get('categorical', []))})**")
            st.write(col_groups.get("categorical", []))
        with sub_c3:
            st.markdown(f"**Text / Other ({len(col_groups.get('text', []))})**")
            st.write(col_groups.get("text", []))

        # Sample records table
        sample_records = metadata.get("sample_records", [])
        if sample_records:
            st.markdown("**Sample Data (First 3 Rows)**")
            st.dataframe(pd.DataFrame(sample_records), use_container_width=True)

    st.markdown("---")

    # Step 2: Natural Language Query & Visualizer Interface
    st.markdown("### 💬 Ask Questions in Natural Language")
    st.write(
        "Ask any statistical question, aggregation request, or chart command. "
        "For example: *'What are the top 5 countries by area?'* or *'Plot a scatter of birth rate vs death rate'*."
    )

    # Quick prompt buttons
    st.markdown("**Sample Prompts:**")
    prompt_col1, prompt_col2, prompt_col3 = st.columns(3)
    preset_query = None

    num_cols = col_groups.get("numeric", [])
    cat_cols = col_groups.get("categorical", [])
    col_a = num_cols[0] if num_cols else "first column"
    col_b = num_cols[1] if len(num_cols) > 1 else col_a
    cat_a = cat_cols[0] if cat_cols else "category"

    with prompt_col1:
        q1 = f"What is the average {col_a}?"
        if st.button(f"🔍 {q1}", key="btn_q1"):
            preset_query = q1
    with prompt_col2:
        q2 = f"Top 5 rows ordered by {col_a}"
        if st.button(f"📈 {q2}", key="btn_q2"):
            preset_query = q2
    with prompt_col3:
        q3 = f"Plot a bar chart of {col_a} by {cat_a}"
        if st.button(f"📊 {q3}", key="btn_q3"):
            preset_query = q3

    query_input = st.text_input(
        "Enter your query:",
        value=preset_query or "",
        placeholder="Type your question here and click Submit...",
        key="clean_query_input",
    )

    submit_clicked = st.button("🚀 Submit Query", type="primary", key="btn_submit_query")

    if submit_clicked and query_input.strip():
        with st.spinner("Analyzing query, generating Python code, and computing answer..."):
            try:
                response = submit_clean_query(
                    file=clean_file,
                    query=query_input.strip(),
                    metadata=metadata,
                )

                # Append to history
                st.session_state["clean_query_history"].insert(0, response)

            except Exception as e:
                st.error("Failed to execute query against the backend.")
                st.exception(e)

    # Display Query Results History
    if st.session_state["clean_query_history"]:
        st.markdown("### 🎯 Results & Insights")

        for idx, item in enumerate(st.session_state["clean_query_history"]):
            with st.container():
                st.markdown(f"#### ❓ Question: *{item.get('query')}*")

                # Natural language answer card
                answer_text = item.get("answer", "")
                if item.get("status") == "success":
                    st.info(answer_text)
                else:
                    st.error(answer_text)

                # Render Interactive Plotly Figure if present
                if item.get("has_figure") and item.get("figure"):
                    try:
                        fig = go.Figure(item["figure"])
                        st.plotly_chart(fig, use_container_width=True)
                    except Exception as fig_err:
                        st.warning(f"Could not render chart: {fig_err}")

                # Render Tabular Data if present
                result_data = item.get("result_data")
                if isinstance(result_data, dict) and result_data.get("type") == "dataframe":
                    records = result_data.get("data", [])
                    if records:
                        st.dataframe(pd.DataFrame(records), use_container_width=True)
                elif isinstance(result_data, dict) and result_data.get("type") == "series":
                    series_dict = result_data.get("data", {})
                    if series_dict:
                        st.dataframe(pd.DataFrame(list(series_dict.items()), columns=["Index", "Value"]), use_container_width=True)

                # Expandable code transparency
                with st.expander(f"⚙️ View Generated Python Code & Execution Log (Attempt {item.get('attempts_count', 1)})"):
                    st.code(item.get("code", "# No code recorded"), language="python")
                    if item.get("stdout"):
                        st.text(f"Console Output:\n{item.get('stdout')}")

                st.markdown("---")
