import os
from pathlib import Path

import pandas as pd
import streamlit as st

from iars_parser import (
    AUDITORS,
    REACTION_OPTIONS,
    FREQUENCY_OPTIONS,
    FINDINGS_DROPDOWN,
    build_records,
    excel_bytes,
)

st.set_page_config(
    page_title="Internal Audit Report System",
    page_icon="📄",
    layout="wide",
)

MASTER_DATA_PATH = Path("data/Master_Data.xlsx")


@st.cache_data(show_spinner=False)
def load_master_data(path: str):
    """Load permanent Master Data from repository."""
    xls = pd.ExcelFile(path)

    employees_df = pd.read_excel(path, sheet_name="Employees") if "Employees" in xls.sheet_names else pd.DataFrame()
    sheets = {
        sheet: pd.read_excel(path, sheet_name=sheet)
        for sheet in xls.sheet_names
    }

    return employees_df, sheets


def save_uploaded_master(uploaded_file):
    """Save uploaded Master Data to app folder.

    Note: On Streamlit Cloud, this persists during the current app runtime/session.
    For permanent update across redeploys, replace data/Master_Data.xlsx in GitHub.
    """
    MASTER_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MASTER_DATA_PATH, "wb") as f:
        f.write(uploaded_file.getbuffer())


st.title("Internal Audit Report System (IARS)")
st.caption("Permanent Master Data + Multiple PDF audit report extraction")

with st.sidebar:
    st.header("Master Data")

    if MASTER_DATA_PATH.exists():
        st.success("Master Data loaded from system.")
        st.caption(str(MASTER_DATA_PATH))
    else:
        st.error("Master Data not found. Upload Master_Data.xlsx first.")

    with st.expander("Update Master Data"):
        uploaded_master = st.file_uploader(
            "Upload updated Master_Data.xlsx",
            type=["xlsx"],
            key="master_update",
        )

        if uploaded_master is not None:
            if st.button("Save Updated Master Data"):
                save_uploaded_master(uploaded_master)
                st.cache_data.clear()
                st.success("Master Data updated. Please refresh the app.")

    st.divider()
    st.header("Audit Reports")
    pdf_files = st.file_uploader(
        "Upload one or multiple audit report PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )


if not MASTER_DATA_PATH.exists():
    st.info("Please upload or add data/Master_Data.xlsx before generating extraction.")
    st.stop()

master_df, master_sheets = load_master_data(str(MASTER_DATA_PATH))

st.subheader("System Status")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Master Data", "Loaded")
with col2:
    st.metric("Employees", len(master_df))
with col3:
    st.metric("PDFs Selected", len(pdf_files) if pdf_files else 0)

if pdf_files:
    st.success(f"{len(pdf_files)} PDF report(s) uploaded successfully.")

    if st.button("Generate Extraction", type="primary"):
        all_results = []
        processing_errors = []

        progress = st.progress(0)
        status = st.empty()

        for idx, pdf_file in enumerate(pdf_files, start=1):
            try:
                status.write(f"Processing {idx} of {len(pdf_files)}: {pdf_file.name}")

                result_df, header, items = build_records(pdf_file, master_df)

                all_results.append(result_df)

            except Exception as e:
                processing_errors.append({
                    "Source PDF": pdf_file.name,
                    "Error": str(e),
                })

            progress.progress(idx / len(pdf_files))

        status.empty()

        if all_results:
            final_df = pd.concat(all_results, ignore_index=True)

            st.subheader("Generated Records")
            st.caption(f"Generated {len(final_df)} finding row(s) from {len(all_results)} processed PDF file(s).")

            edited_result = st.data_editor(
                final_df,
                use_container_width=True,
                num_rows="fixed",
                column_config={
                    "Findings": st.column_config.SelectboxColumn(
                        "Findings",
                        options=FINDINGS_DROPDOWN,
                    ),
                    "Audited By1": st.column_config.SelectboxColumn(
                        "Audited By1",
                        options=[""] + AUDITORS,
                    ),
                    "Reaction": st.column_config.SelectboxColumn(
                        "Reaction",
                        options=REACTION_OPTIONS,
                    ),
                    "Frequency": st.column_config.SelectboxColumn(
                        "Frequency",
                        options=FREQUENCY_OPTIONS,
                    ),
                },
            )

            st.download_button(
                "Download Consolidated Excel Output",
                data=excel_bytes(edited_result),
                file_name="audit_extraction_consolidated.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        if processing_errors:
            st.warning("Some PDF files were not processed.")
            st.dataframe(pd.DataFrame(processing_errors), use_container_width=True)

else:
    st.info("Upload one or multiple audit report PDFs to start.")
