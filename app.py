
import pandas as pd
import streamlit as st
from iars_parser import (
    AUDITORS, REACTION_OPTIONS, FREQUENCY_OPTIONS, FINDINGS_DROPDOWN,
    build_records, excel_bytes
)

st.set_page_config(page_title="Internal Audit Report System V2", page_icon="📄", layout="wide")

st.title("Internal Audit Report System (IARS) - V2 Structured Parser")
st.caption("Table-based PDF extraction. This version uses PDF tables first to prevent mixed issue/recommendation text.")

with st.sidebar:
    st.header("Uploads")
    master_file = st.file_uploader("Upload Employee Masterlist", type=["xlsx", "csv"])
    pdf_file = st.file_uploader("Upload Audit Report PDF", type=["pdf"])

master_df = None
if master_file:
    master_df = pd.read_csv(master_file) if master_file.name.lower().endswith(".csv") else pd.read_excel(master_file)
    st.success("Employee masterlist loaded.")
    st.dataframe(master_df.head(20), use_container_width=True)

if pdf_file:
    # Build first pass to show detected issue rows.
    result_df, header, items = build_records(pdf_file, master_df)

    st.subheader("Detected Header")
    st.json(header)

    st.subheader("Detected Issues")
    issue_preview = pd.DataFrame([
        {
            "Issue No.": x["issue_no"],
            "Issue": x["issue"],
            "Recommendation1": x["recommendation1"],
            "Explanation": x["explanation"],
            "Correction": x["correction"],
        }
        for x in items
    ])
    st.dataframe(issue_preview, use_container_width=True)

    st.subheader("Manual Inputs Per Issue")
    manual_df = pd.DataFrame([
        {
            "Issue No.": x["issue_no"],
            "Detected Issue": x["issue"],
            "Task ID": "",
            "Auditor": "",
            "Reaction": "",
            "Frequency": "",
        }
        for x in items
    ])

    edited_manual = st.data_editor(
        manual_df,
        use_container_width=True,
        num_rows="fixed",
        column_config={
            "Auditor": st.column_config.SelectboxColumn("Auditor", options=[""] + AUDITORS),
            "Reaction": st.column_config.SelectboxColumn("Reaction", options=REACTION_OPTIONS),
            "Frequency": st.column_config.SelectboxColumn("Frequency", options=FREQUENCY_OPTIONS),
        }
    )

    if st.button("Generate Final Extraction", type="primary"):
        pdf_file.seek(0)
        final_df, final_header, final_items = build_records(pdf_file, master_df, edited_manual)

        st.subheader("Generated Records")
        edited_result = st.data_editor(
            final_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "Findings": st.column_config.SelectboxColumn("Findings", options=FINDINGS_DROPDOWN),
                "Auditor": st.column_config.SelectboxColumn("Audited By1", options=[""] + AUDITORS),
                "Reaction": st.column_config.SelectboxColumn("Reaction", options=REACTION_OPTIONS),
                "Frequency": st.column_config.SelectboxColumn("Frequency", options=FREQUENCY_OPTIONS),
            }
        )

        st.download_button(
            "Download Excel Output",
            data=excel_bytes(edited_result),
            file_name="audit_extraction_output_v2.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Upload the Employee Masterlist and Audit PDF to start.")
