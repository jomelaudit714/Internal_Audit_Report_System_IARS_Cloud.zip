
from pathlib import Path
from io import BytesIO

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


def render_pdf_page(pdf_bytes: bytes, page_no: int, zoom: float = 1.4):
    """Render a PDF page to PNG for preview."""
    try:
        import fitz
        from PIL import Image
    except Exception:
        return None, None, None

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc.load_page(page_no)
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img, page.rect.width, page.rect.height


def stamp_pdf_with_tags(pdf_bytes: bytes, tag_rows):
    """Insert typed tags into the PDF at normalized positions."""
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for row in tag_rows:
        label_text = str(row.get("Label Text", "") or "").strip()
        if not label_text:
            continue

        try:
            page_index = int(row.get("Page", 1)) - 1
            x_percent = float(row.get("X %", 8))
            y_percent = float(row.get("Y %", 12))
            font_size = float(row.get("Font Size", 11))
        except Exception:
            continue

        if page_index < 0 or page_index >= len(doc):
            continue

        page = doc.load_page(page_index)
        x = max(0, min(100, x_percent)) / 100 * page.rect.width
        y = max(0, min(100, y_percent)) / 100 * page.rect.height

        # Black text is the safest for OCR and normal PDF text extraction.
        page.insert_text(
            fitz.Point(x, y),
            label_text,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
        )

    output = BytesIO()
    doc.save(output)
    output.seek(0)
    return output.getvalue()


def normalize_tag_text(tag_type: str, value: str):
    tag_type = str(tag_type or "").strip()
    value = str(value or "").strip()
    if not value:
        return ""

    mapping = {
        "Task ID": "Task ID",
        "Auditor": "Auditor",
        "Auditee": "Auditee",
        "Frequency Rate": "Frequency Rate",
        "Reaction": "Reaction",
    }
    label = mapping.get(tag_type, tag_type)
    return f"{label}: {value}"


def build_default_tag_rows(page_count: int = 1):
    return pd.DataFrame(
        [
            {"Page": 1, "Tag Type": "Task ID", "Value": "001", "Label Text": "Task ID: 001", "X %": 8.0, "Y %": 24.0, "Font Size": 11},
            {"Page": 1, "Tag Type": "Auditor", "Value": "Patricia Anne S. Del Rosario", "Label Text": "Auditor: Patricia Anne S. Del Rosario", "X %": 8.0, "Y %": 27.0, "Font Size": 11},
            {"Page": 1, "Tag Type": "Auditee", "Value": "Emerito Bondoc", "Label Text": "Auditee: Emerito Bondoc", "X %": 8.0, "Y %": 30.0, "Font Size": 11},
        ]
    )


st.title("Internal Audit Report System (IARS)")
st.caption("Permanent Master Data + Multiple PDF audit report extraction + PDF Tagging Editor")

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

if not MASTER_DATA_PATH.exists():
    st.info("Please upload or add data/Master_Data.xlsx before generating extraction.")
    st.stop()

master_df, master_sheets = load_master_data(str(MASTER_DATA_PATH))
auditors_df = master_sheets.get("Auditors", pd.DataFrame())
auditor_options = auditors_df["Auditor"].dropna().astype(str).tolist() if not auditors_df.empty and "Auditor" in auditors_df.columns else AUDITORS

tab_extract, tab_editor = st.tabs(["Generate Extraction", "PDF Tagging Editor"])


with tab_editor:
    st.subheader("PDF Tagging Editor")
    st.caption(
        "Use this instead of handwriting. Click the PDF preview, type the tag in the popup form, then generate a tagged PDF."
    )

    tag_pdf = st.file_uploader(
        "Upload PDF to tag",
        type=["pdf"],
        key="tag_pdf_upload",
    )

    if tag_pdf is not None:
        pdf_bytes = tag_pdf.getvalue()

        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
        except Exception as e:
            st.error(f"Unable to open PDF: {e}")
            page_count = 0

        if page_count:
            if "tag_rows" not in st.session_state:
                st.session_state["tag_rows"] = pd.DataFrame(
                    columns=["Page", "Tag Type", "Value", "Label Text", "X %", "Y %", "Font Size"]
                )
            if "pending_click" not in st.session_state:
                st.session_state["pending_click"] = None

            st.info(
                "Workflow: choose a page → click where the label should appear → fill in the popup form → save tag → generate tagged PDF."
            )

            col_left, col_right = st.columns([1.25, 1])

            with col_left:
                preview_page = st.number_input(
                    "Page to tag",
                    min_value=1,
                    max_value=page_count,
                    value=1,
                    step=1,
                    key="click_preview_page",
                )

                preview_img, page_w, page_h = render_pdf_page(pdf_bytes, int(preview_page) - 1)

                st.markdown("#### Click on the page")
                st.caption("After clicking, a tag form will appear on the right.")

                clicked_x = None
                clicked_y = None

                try:
                    from streamlit_image_coordinates import streamlit_image_coordinates

                    if preview_img is not None:
                        click = streamlit_image_coordinates(
                            preview_img,
                            key=f"pdf_click_coordinates_{preview_page}",
                        )

                        if click is not None:
                            clicked_x = float(click.get("x", 0))
                            clicked_y = float(click.get("y", 0))
                            img_w, img_h = preview_img.size
                            st.session_state["pending_click"] = {
                                "page": int(preview_page),
                                "x_percent": round((clicked_x / img_w) * 100, 2),
                                "y_percent": round((clicked_y / img_h) * 100, 2),
                            }

                    else:
                        st.warning("Preview requires PyMuPDF and Pillow.")

                except Exception:
                    if preview_img is not None:
                        st.image(preview_img, caption=f"Page {preview_page} preview")
                    st.warning(
                        "Clickable preview component is not installed. Use manual X/Y fields on the right instead."
                    )

                # Show current tags for selected page.
                current_tags = st.session_state["tag_rows"]
                if not current_tags.empty:
                    page_tags = current_tags[current_tags["Page"].astype(str) == str(int(preview_page))]
                    if not page_tags.empty:
                        st.markdown("#### Tags on this page")
                        st.dataframe(
                            page_tags[["Label Text", "X %", "Y %"]],
                            use_container_width=True,
                            hide_index=True,
                        )

            with col_right:
                st.markdown("### Add Tag Popup")

                pending = st.session_state.get("pending_click")
                if pending:
                    st.success(
                        f"Selected location: Page {pending['page']} | X {pending['x_percent']}% | Y {pending['y_percent']}%"
                    )
                    default_page = pending["page"]
                    default_x = pending["x_percent"]
                    default_y = pending["y_percent"]
                else:
                    st.caption("No click yet. You may still manually enter the location.")
                    default_page = int(preview_page)
                    default_x = 8.0
                    default_y = 24.0

                with st.form("click_tag_form", clear_on_submit=False):
                    form_page = st.number_input(
                        "Page",
                        min_value=1,
                        max_value=page_count,
                        value=int(default_page),
                        step=1,
                    )

                    tag_type = st.selectbox(
                        "Tag Type",
                        ["Task ID", "Auditor", "Auditee", "Frequency Rate", "Reaction"],
                    )

                    if tag_type == "Auditor":
                        tag_value = st.selectbox("Value", [""] + auditor_options)
                    elif tag_type == "Reaction":
                        tag_value = st.selectbox("Value", [""] + REACTION_OPTIONS)
                    elif tag_type == "Frequency Rate":
                        tag_value = st.selectbox("Value", [""] + FREQUENCY_OPTIONS)
                    else:
                        tag_value = st.text_input("Value", placeholder="Example: 001 or Emerito Bondoc")

                    cxy1, cxy2 = st.columns(2)
                    with cxy1:
                        form_x = st.number_input(
                            "X position (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(default_x),
                            step=0.5,
                        )
                    with cxy2:
                        form_y = st.number_input(
                            "Y position (%)",
                            min_value=0.0,
                            max_value=100.0,
                            value=float(default_y),
                            step=0.5,
                        )

                    font_size = st.number_input(
                        "Font size",
                        min_value=6.0,
                        max_value=24.0,
                        value=11.0,
                        step=1.0,
                    )

                    label_text = normalize_tag_text(tag_type, tag_value)
                    st.text_input("Text to insert", value=label_text, disabled=True)

                    submitted = st.form_submit_button("Save Tag Here", type="primary")

                if submitted:
                    if not label_text:
                        st.warning("Please enter a value before saving the tag.")
                    else:
                        new_row = pd.DataFrame([{
                            "Page": int(form_page),
                            "Tag Type": tag_type,
                            "Value": tag_value,
                            "Label Text": label_text,
                            "X %": float(form_x),
                            "Y %": float(form_y),
                            "Font Size": float(font_size),
                        }])
                        st.session_state["tag_rows"] = pd.concat(
                            [st.session_state["tag_rows"], new_row],
                            ignore_index=True,
                        )
                        st.session_state["pending_click"] = None
                        st.success(f"Saved: {label_text}")

                st.divider()
                st.markdown("### Quick Add Buttons")
                st.caption("Common tags; click page first, then press one of these buttons.")

                q1, q2, q3 = st.columns(3)
                with q1:
                    quick_task = st.text_input("Task ID", value="001", key="quick_task_id")
                    if st.button("Add Task ID"):
                        pending = st.session_state.get("pending_click")
                        if pending:
                            label_text = f"Task ID: {quick_task}"
                            new_row = pd.DataFrame([{
                                "Page": int(pending["page"]),
                                "Tag Type": "Task ID",
                                "Value": quick_task,
                                "Label Text": label_text,
                                "X %": float(pending["x_percent"]),
                                "Y %": float(pending["y_percent"]),
                                "Font Size": 11.0,
                            }])
                            st.session_state["tag_rows"] = pd.concat(
                                [st.session_state["tag_rows"], new_row],
                                ignore_index=True,
                            )
                            st.session_state["pending_click"] = None
                            st.rerun()
                        else:
                            st.warning("Click the PDF page first.")
                with q2:
                    quick_auditor = st.selectbox("Auditor", [""] + auditor_options, key="quick_auditor")
                    if st.button("Add Auditor"):
                        pending = st.session_state.get("pending_click")
                        if pending and quick_auditor:
                            label_text = f"Auditor: {quick_auditor}"
                            new_row = pd.DataFrame([{
                                "Page": int(pending["page"]),
                                "Tag Type": "Auditor",
                                "Value": quick_auditor,
                                "Label Text": label_text,
                                "X %": float(pending["x_percent"]),
                                "Y %": float(pending["y_percent"]),
                                "Font Size": 11.0,
                            }])
                            st.session_state["tag_rows"] = pd.concat(
                                [st.session_state["tag_rows"], new_row],
                                ignore_index=True,
                            )
                            st.session_state["pending_click"] = None
                            st.rerun()
                        else:
                            st.warning("Click the PDF page first and select an auditor.")
                with q3:
                    quick_auditee = st.text_input("Auditee", value="", key="quick_auditee")
                    if st.button("Add Auditee"):
                        pending = st.session_state.get("pending_click")
                        if pending and quick_auditee:
                            label_text = f"Auditee: {quick_auditee}"
                            new_row = pd.DataFrame([{
                                "Page": int(pending["page"]),
                                "Tag Type": "Auditee",
                                "Value": quick_auditee,
                                "Label Text": label_text,
                                "X %": float(pending["x_percent"]),
                                "Y %": float(pending["y_percent"]),
                                "Font Size": 11.0,
                            }])
                            st.session_state["tag_rows"] = pd.concat(
                                [st.session_state["tag_rows"], new_row],
                                ignore_index=True,
                            )
                            st.session_state["pending_click"] = None
                            st.rerun()
                        else:
                            st.warning("Click the PDF page first and enter an auditee.")

            st.divider()
            st.markdown("### Tag List")
            tag_rows = st.data_editor(
                st.session_state["tag_rows"],
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Page": st.column_config.NumberColumn("Page", min_value=1, max_value=page_count, step=1),
                    "Tag Type": st.column_config.SelectboxColumn(
                        "Tag Type",
                        options=["Task ID", "Auditor", "Auditee", "Frequency Rate", "Reaction"],
                    ),
                    "X %": st.column_config.NumberColumn("X %", min_value=0.0, max_value=100.0, step=0.5),
                    "Y %": st.column_config.NumberColumn("Y %", min_value=0.0, max_value=100.0, step=0.5),
                    "Font Size": st.column_config.NumberColumn("Font Size", min_value=6.0, max_value=24.0, step=1.0),
                },
            )
            st.session_state["tag_rows"] = tag_rows

            cgen, cclear = st.columns([1, 1])
            with cgen:
                if st.button("Generate Tagged PDF", type="primary"):
                    try:
                        tagged_bytes = stamp_pdf_with_tags(pdf_bytes, tag_rows.to_dict("records"))
                        st.success("Tagged PDF created. Download it, then upload it in Generate Extraction.")
                        st.download_button(
                            "Download Tagged PDF",
                            data=tagged_bytes,
                            file_name=f"tagged_{tag_pdf.name}",
                            mime="application/pdf",
                        )
                    except Exception as e:
                        st.error(f"Unable to generate tagged PDF: {e}")
            with cclear:
                if st.button("Clear All Tags"):
                    st.session_state["tag_rows"] = pd.DataFrame(
                        columns=["Page", "Tag Type", "Value", "Label Text", "X %", "Y %", "Font Size"]
                    )
                    st.session_state["pending_click"] = None
                    st.rerun()

    else:
        st.info("Upload a PDF to start tagging.")

with tab_extract:
    st.subheader("System Status")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Master Data", "Loaded")
    with col2:
        st.metric("Employees", len(master_df))

    st.divider()
    st.header("Audit Reports")
    pdf_files = st.file_uploader(
        "Upload one or multiple audit report PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="extract_pdf_upload",
    )

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

                    result_df, header, items = build_records(pdf_file, master_df, auditors_df=auditors_df)
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
                            options=[""] + auditor_options,
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
