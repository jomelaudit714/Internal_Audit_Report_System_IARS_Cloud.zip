import pandas as pd
import streamlit as st
from iars_parser import (
    AUDITORS, REACTION_OPTIONS, FREQUENCY_OPTIONS, FINDINGS_DROPDOWN,
    build_records, excel_bytes
)

st.set_page_config(
    page_title="Internal Audit Report System",
    page_icon="📄",
    layout="wide"
)

st.title("Internal Audit Report System (IARS)")
st.caption("Audit PDF extraction and Excel generation.")

with st.sidebar:
    st.header("Upload Files")
    master_file = st.file_uploader("Employee Masterlist", type=["xlsx", "csv"])
    pdf_file = st.file_uploader("Audit Report PDF", type=["pdf"])

master_df = None

if master_file:
    master_df = (
        pd.read_csv(master_file)
        if master_file.name.lower().endswith(".csv")
        else pd.read_excel(master_file)
    )
    st.success("Employee Masterlist uploaded successfully.")

if pdf_file:
    st.success("Audit Report PDF uploaded successfully.")

    if st.button("Generate Extraction", type="primary"):
        result_df, header, items = build_records(pdf_file, master_df)

        st.subheader("Generated Records")

        edited_result = st.data_editor(
            result_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Findings": st.column_config.SelectboxColumn(
                    "Findings",
                    options=FINDINGS_DROPDOWN
                ),
                "Audited By1": st.column_config.SelectboxColumn(
                    "Audited By1",
                    options=[""] + AUDITORS
                ),
                "Reaction": st.column_config.SelectboxColumn(
                    "Reaction",
                    options=REACTION_OPTIONS
                ),
                "Frequency": st.column_config.SelectboxColumn(
                    "Frequency",
                    options=FREQUENCY_OPTIONS
                ),
            }
        )

        st.download_button(
            "Download Excel Output",
            data=excel_bytes(edited_result),
            file_name="audit_extraction_output.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Upload the Employee Masterlist and Audit Report PDF to start.")
