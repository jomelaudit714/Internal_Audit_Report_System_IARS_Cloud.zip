
from pathlib import Path
from io import BytesIO
import base64
import hashlib

import pandas as pd
import streamlit as st

from iars_pdf_editor import pdf_textbox_editor

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


def draw_preview_box(img, x_percent, y_percent, box_width_px=220, box_height_px=32):
    """Draw a visible temporary box on the preview image before saving the tag."""
    try:
        from PIL import ImageDraw
    except Exception:
        return img

    if img is None:
        return img

    preview = img.copy()
    draw = ImageDraw.Draw(preview)
    img_w, img_h = preview.size

    x = float(x_percent) / 100 * img_w
    y = float(y_percent) / 100 * img_h

    rect = [
        x,
        y - box_height_px / 2,
        min(img_w - 1, x + box_width_px),
        min(img_h - 1, y + box_height_px / 2),
    ]

    # Multiple outlines make it visible without relying on a specific color too much.
    draw.rectangle(rect, outline="black", width=3)
    draw.rectangle([rect[0]+3, rect[1]+3, rect[2]-3, rect[3]-3], outline="white", width=2)
    return preview


def stamp_pdf_with_tags(pdf_bytes: bytes, tag_rows):
    """Insert typed PDF editor tags using percentage-based coordinates."""
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
            width_percent = float(row.get("Width %", 30))
            height_percent = float(row.get("Height %", 6))
            font_size = float(row.get("Font Size", 11))
            style = str(row.get("Style", "Box") or "Box")
        except (TypeError, ValueError):
            continue

        if page_index < 0 or page_index >= len(doc):
            continue

        page = doc.load_page(page_index)
        x0 = max(0, min(100, x_percent)) / 100 * page.rect.width
        y0 = max(0, min(100, y_percent)) / 100 * page.rect.height
        width = max(2, min(100, width_percent)) / 100 * page.rect.width
        height = max(1, min(100, height_percent)) / 100 * page.rect.height
        x1 = min(page.rect.width, x0 + width)
        y1 = min(page.rect.height, y0 + height)
        rect = fitz.Rect(x0, y0, x1, y1)

        if style == "Highlight Box":
            page.draw_rect(rect, color=(0, 0, 0), fill=(1, 1, 0.65), width=0.8)
        elif style == "Box":
            page.draw_rect(rect, color=(0, 0, 0), fill=(1, 1, 1), width=0.8)

        text_rect = fitz.Rect(rect.x0 + 4, rect.y0 + 3, rect.x1 - 4, rect.y1 - 3)
        remaining = page.insert_textbox(
            text_rect,
            label_text,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
            align=fitz.TEXT_ALIGN_LEFT,
        )

        # If the user's box is too small, retry with a slightly smaller font so
        # the essential tag remains visible and machine-readable.
        if remaining < 0 and font_size > 7:
            page.insert_textbox(
                text_rect,
                label_text,
                fontsize=max(7, font_size - 2),
                fontname="helv",
                color=(0, 0, 0),
                align=fitz.TEXT_ALIGN_LEFT,
            )

    output = BytesIO()
    doc.save(output, garbage=4, deflate=True)
    output.seek(0)
    return output.getvalue()


def image_to_data_uri(image):
    """Convert a rendered PIL page image to a browser-ready data URI."""
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def editor_file_id(file_name: str, pdf_bytes: bytes) -> str:
    digest = hashlib.sha256(pdf_bytes).hexdigest()[:12]
    safe_name = "".join(ch if ch.isalnum() else "_" for ch in file_name)[:40]
    return f"{safe_name}_{digest}"


def component_editor_value(state):
    """Read a Components v2 state value from dict-like or result objects."""
    if state is None:
        return {"boxes": [], "selected_id": None}
    if isinstance(state, dict):
        return state.get("editor", {"boxes": [], "selected_id": None})
    return getattr(state, "editor", {"boxes": [], "selected_id": None})


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
            {"Page": 1, "Tag Type": "Task ID", "Value": "001", "Label Text": "Task ID: 001", "X %": 8.0, "Y %": 24.0, "Font Size": 11, "Style": "Box", "Box Width": 160, "Box Height": 24},
            {"Page": 1, "Tag Type": "Auditor", "Value": "Patricia Anne S. Del Rosario", "Label Text": "Auditor: Patricia Anne S. Del Rosario", "X %": 8.0, "Y %": 27.0, "Font Size": 11, "Style": "Box", "Box Width": 280, "Box Height": 24},
            {"Page": 1, "Tag Type": "Auditee", "Value": "Emerito Bondoc", "Label Text": "Auditee: Emerito Bondoc", "X %": 8.0, "Y %": 30.0, "Font Size": 11, "Style": "Box", "Box Width": 230, "Box Height": 24},
        ]
    )


st.title("Internal Audit Report System (IARS)")
st.caption("Permanent Master Data + Multiple PDF extraction + PDF Textbox Editor v2.2")

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
        "Double-right-click the PDF to add a textbox. Click inside to type, "
        "drag the top strip to reposition, and drag the blue handles to resize."
    )

    tag_pdf = st.file_uploader(
        "Upload PDF to tag",
        type=["pdf"],
        key="tag_pdf_upload",
    )

    if tag_pdf is not None:
        pdf_bytes = tag_pdf.getvalue()
        file_id = editor_file_id(tag_pdf.name, pdf_bytes)

        try:
            import fitz

            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            page_count = len(doc)
        except Exception as exc:
            st.error(f"Unable to open PDF: {exc}")
            page_count = 0

        if page_count:
            clear_request_key = f"clear_pdf_editor_request_{file_id}"
            if st.session_state.pop(clear_request_key, False):
                for state_key in list(st.session_state.keys()):
                    if state_key.startswith(f"iars_pdf_editor_{file_id}_page_"):
                        del st.session_state[state_key]
                st.session_state.pop(f"tagged_pdf_{file_id}", None)

            controls_left, controls_right = st.columns([1, 2])
            with controls_left:
                preview_page = st.number_input(
                    "Page to tag",
                    min_value=1,
                    max_value=page_count,
                    value=1,
                    step=1,
                    key=f"editor_page_{file_id}",
                )
            with controls_right:
                st.info(
                    "First right-click marks the location; right-click the same spot again "
                    "to create the textbox. The browser menu is suppressed inside the PDF."
                )

            preview_img, page_width, page_height = render_pdf_page(
                pdf_bytes,
                int(preview_page) - 1,
                zoom=1.7,
            )

            if preview_img is None:
                st.error("Unable to render this PDF page.")
            else:
                component_key = f"iars_pdf_editor_{file_id}_page_{int(preview_page)}"
                current_state = st.session_state.get(component_key, {})
                initial_editor = component_editor_value(current_state)
                initial_boxes = initial_editor.get("boxes", [])

                editor_result = pdf_textbox_editor(
                    image_data=image_to_data_uri(preview_img),
                    initial_boxes=initial_boxes,
                    key=component_key,
                    height=940,
                )

                current_editor = component_editor_value(editor_result)
                boxes = current_editor.get("boxes", [])
                nonempty_boxes = [box for box in boxes if str(box.get("text", "")).strip()]
                st.caption(
                    f"Page {int(preview_page)}: {len(boxes)} textbox(es), "
                    f"{len(nonempty_boxes)} containing text."
                )

            all_tag_rows = []
            for page_number in range(1, page_count + 1):
                page_key = f"iars_pdf_editor_{file_id}_page_{page_number}"
                page_editor = component_editor_value(st.session_state.get(page_key, {}))
                for box in page_editor.get("boxes", []):
                    label_text = str(box.get("text", "") or "").strip()
                    if not label_text:
                        continue
                    all_tag_rows.append(
                        {
                            "Page": page_number,
                            "Label Text": label_text,
                            "X %": float(box.get("x_pct", 0)),
                            "Y %": float(box.get("y_pct", 0)),
                            "Width %": float(box.get("w_pct", 30)),
                            "Height %": float(box.get("h_pct", 6)),
                            "Font Size": float(box.get("font_size", 11)),
                            "Style": str(box.get("style", "Box")),
                        }
                    )

            if all_tag_rows:
                with st.expander(f"Review saved textbox data ({len(all_tag_rows)})"):
                    st.dataframe(pd.DataFrame(all_tag_rows), width="stretch", hide_index=True)
            else:
                st.info("No completed textbox tags yet. You may proceed without tags or add them in the editor.")

            action_left, action_middle, action_right = st.columns([1, 1, 1])
            with action_left:
                if st.button("Generate Tagged PDF", type="primary", disabled=not all_tag_rows):
                    try:
                        tagged_bytes = stamp_pdf_with_tags(pdf_bytes, all_tag_rows)
                        st.session_state[f"tagged_pdf_{file_id}"] = tagged_bytes
                        st.success("Tagged PDF generated successfully.")
                    except Exception as exc:
                        st.error(f"Unable to generate tagged PDF: {exc}")

            with action_middle:
                tagged_pdf = st.session_state.get(f"tagged_pdf_{file_id}")
                if tagged_pdf:
                    st.download_button(
                        "Download Tagged PDF",
                        data=tagged_pdf,
                        file_name=f"tagged_{tag_pdf.name}",
                        mime="application/pdf",
                    )

            with action_right:
                if st.button("Clear All PDF Tags"):
                    st.session_state[clear_request_key] = True
                    st.rerun()
    else:
        st.info("Upload a PDF only when tags are needed. Otherwise, use Generate Extraction directly.")

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
                    width="stretch",
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
                st.dataframe(pd.DataFrame(processing_errors), width="stretch")

    else:
        st.info("Upload one or multiple audit report PDFs to start.")
