import streamlit as st

from api import analyze_dataset
from components.report import display_report


st.set_page_config(
    page_title="EDA-Guider",
    page_icon="📊",
    layout="wide",
)


st.title("EDA-Guider")

st.write(
    "Automated Exploratory Data Analysis "
    "for your dataset."
)


uploaded_file = st.file_uploader(
    "Upload your dataset",
    type=[
        "csv",
        "tsv",
        "xlsx",
        "xls",
        "xlsm",
    ],
)


if uploaded_file is not None:

    st.success(
        f"File selected: {uploaded_file.name}"
    )

    if st.button(
        "Generate EDA Report",
        type="primary",
    ):

        with st.spinner(
            "Analyzing your dataset..."
        ):

            try:

                result = analyze_dataset(
                    uploaded_file
                )

                if result.get("status") != "success":

                    st.error(
                        "EDA analysis failed."
                    )

                else:

                    st.success(
                        "EDA report generated successfully."
                    )

                    display_report(
                        result
                    )

            except Exception as error:

                st.error(
                    "Failed to communicate with "
                    "the EDA backend."
                )

                st.exception(error)