
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
    """Insert typed tags into the PDF at normalized positions.

    Supports:
    - Plain Text
    - Box
    - Highlight Box
    """
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
            box_width = float(row.get("Box Width", 210))
            box_height = float(row.get("Box Height", 22))
            style = str(row.get("Style", "Box") or "Box")
        except Exception:
            continue

        if page_index < 0 or page_index >= len(doc):
            continue

        page = doc.load_page(page_index)
        x = max(0, min(100, x_percent)) / 100 * page.rect.width
        y = max(0, min(100, y_percent)) / 100 * page.rect.height

        if style in ["Box", "Highlight Box"]:
            rect = fitz.Rect(x, y - font_size - 5, x + box_width, y + box_height - font_size - 5)

            if style == "Highlight Box":
                page.draw_rect(
                    rect,
                    color=(0, 0, 0),
                    fill=(1, 1, 0.65),
                    width=0.8,
                )
            else:
                page.draw_rect(
                    rect,
                    color=(0, 0, 0),
                    fill=(1, 1, 1),
                    width=0.8,
                )

            text_point = fitz.Point(rect.x0 + 5, rect.y0 + font_size + 2)
            page.insert_text(
                text_point,
                label_text,
                fontsize=font_size,
                fontname="helv",
                color=(0, 0, 0),
            )
        else:
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
            {"Page": 1, "Tag Type": "Task ID", "Value": "001", "Label Text": "Task ID: 001", "X %": 8.0, "Y %": 24.0, "Font Size": 11, "Style": "Box", "Box Width": 160, "Box Height": 24},
            {"Page": 1, "Tag Type": "Auditor", "Value": "Patricia Anne S. Del Rosario", "Label Text": "Auditor: Patricia Anne S. Del Rosario", "X %": 8.0, "Y %": 27.0, "Font Size": 11, "Style": "Box", "Box Width": 280, "Box Height": 24},
            {"Page": 1, "Tag Type": "Auditee", "Value": "Emerito Bondoc", "Label Text": "Auditee: Emerito Bondoc", "X %": 8.0, "Y %": 30.0, "Font Size": 11, "Style": "Box", "Box Width": 230, "Box Height": 24},
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
        "Draw a box directly on the PDF like a simple PDF editor. Then enter the tag text and save it."
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
                    columns=["Page", "Tag Type", "Value", "Label Text", "X %", "Y %", "Font Size", "Style", "Box Width", "Box Height"]
                )

            st.info(
                "If no tag is needed, go directly to Generate Extraction. If a tag is needed: draw a box on the PDF, enter the label below, save tag, then generate tagged PDF."
            )

            preview_page = st.number_input(
                "Page to tag",
                min_value=1,
                max_value=page_count,
                value=1,
                step=1,
                key="drawable_preview_page",
            )

            # Render larger page preview for tagging.
            preview_img, page_w, page_h = render_pdf_page(pdf_bytes, int(preview_page) - 1, zoom=1.9)

            st.markdown("### Draw Box on PDF")
            st.caption(
                "Use your mouse to draw a rectangle where the tag should appear. To change size/place, clear and draw again. This is smoother than click popups."
            )

            canvas_result = None
            selected_rect = None

            try:
                from streamlit_drawable_canvas import st_canvas

                if preview_img is not None:
                    img_w, img_h = preview_img.size

                    canvas_result = st_canvas(
                        fill_color="rgba(255, 255, 150, 0.25)",
                        stroke_width=2,
                        stroke_color="#000000",
                        background_image=preview_img,
                        update_streamlit=True,
                        height=img_h,
                        width=img_w,
                        drawing_mode="rect",
                        key=f"pdf_box_canvas_{preview_page}",
                    )

                    if canvas_result is not None and canvas_result.json_data is not None:
                        objects = canvas_result.json_data.get("objects", [])
                        rects = [obj for obj in objects if obj.get("type") == "rect"]
                        if rects:
                            selected_rect = rects[-1]
                else:
                    st.warning("Preview requires PyMuPDF and Pillow.")

            except Exception as e:
                st.warning(
                    "Drawable box editor is not available. Please check that streamlit-drawable-canvas is installed."
                )
                if preview_img is not None:
                    st.image(preview_img, caption=f"Page {preview_page} preview")
                selected_rect = None

            if selected_rect:
                img_w, img_h = preview_img.size
                left = float(selected_rect.get("left", 0))
                top = float(selected_rect.get("top", 0))
                width = float(selected_rect.get("width", 0)) * float(selected_rect.get("scaleX", 1))
                height = float(selected_rect.get("height", 0)) * float(selected_rect.get("scaleY", 1))

                x_percent = round((left / img_w) * 100, 2)
                y_percent = round(((top + height) / img_h) * 100, 2)

                # Convert preview pixels to PDF points approximately based on rendered page size.
                pdf_box_width = max(60.0, (width / img_w) * float(page_w))
                pdf_box_height = max(16.0, (height / img_h) * float(page_h))

                st.success(
                    f"Box ready: Page {preview_page} | X {x_percent}% | Y {y_percent}% | Width {round(pdf_box_width, 1)} | Height {round(pdf_box_height, 1)}"
                )

                st.markdown("### Enter Text for the Box")

                with st.form("drawable_tag_form", clear_on_submit=False):
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

                    font_size = st.number_input(
                        "Font size",
                        min_value=6.0,
                        max_value=24.0,
                        value=11.0,
                        step=1.0,
                    )

                    style = st.selectbox(
                        "Display style",
                        ["Box", "Highlight Box", "Plain Text"],
                        index=0,
                    )

                    label_text = normalize_tag_text(tag_type, tag_value)
                    st.text_input("Text to insert", value=label_text, disabled=True)

                    submitted = st.form_submit_button("Save This Box Tag", type="primary")

                if submitted:
                    if not label_text:
                        st.warning("Please enter a value before saving the tag.")
                    else:
                        new_row = pd.DataFrame([{
                            "Page": int(preview_page),
                            "Tag Type": tag_type,
                            "Value": tag_value,
                            "Label Text": label_text,
                            "X %": float(x_percent),
                            "Y %": float(y_percent),
                            "Font Size": float(font_size),
                            "Style": style,
                            "Box Width": float(pdf_box_width),
                            "Box Height": float(pdf_box_height),
                        }])
                        st.session_state["tag_rows"] = pd.concat(
                            [st.session_state["tag_rows"], new_row],
                            ignore_index=True,
                        )
                        st.success(f"Saved: {label_text}")
                        st.caption("Draw another box if you need another tag.")

            else:
                st.info("Draw a box on the PDF first. The tag input form will appear after a box is detected.")

            st.divider()
            st.markdown("### Saved Tags")
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
                    "Style": st.column_config.SelectboxColumn(
                        "Style",
                        options=["Box", "Highlight Box", "Plain Text"],
                    ),
                    "Box Width": st.column_config.NumberColumn("Box Width", min_value=60.0, max_value=500.0, step=10.0),
                    "Box Height": st.column_config.NumberColumn("Box Height", min_value=16.0, max_value=120.0, step=2.0),
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
                if st.button("Clear All Saved Tags"):
                    st.session_state["tag_rows"] = pd.DataFrame(
                        columns=["Page", "Tag Type", "Value", "Label Text", "X %", "Y %", "Font Size", "Style", "Box Width", "Box Height"]
                    )
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
