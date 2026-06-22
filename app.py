
from pathlib import Path
from io import BytesIO
from datetime import date
import base64
import hashlib

import pandas as pd
import streamlit as st

from iars_pdf_editor import pdf_textbox_editor

from iars_archive import (
    ArchiveConfig,
    ArchiveError,
    ArchiveNotConfiguredError,
    DuplicateArchiveError,
    archive_is_configured,
    create_archive_client,
    delete_pdf as delete_archived_pdf,
    download_pdf as download_archived_pdf,
    extract_archive_metadata,
    filter_records as filter_archive_records,
    human_file_size,
    list_records as list_archive_records,
    read_archive_config,
    upload_pdf as upload_archived_pdf,
)

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
    """Insert single-line PDF tags with tight padding and automatic font fitting."""
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for row in tag_rows:
        label_text = " ".join(str(row.get("Label Text", "") or "").split())
        if not label_text:
            continue

        try:
            page_index = int(row.get("Page", 1)) - 1
            x_percent = float(row.get("X %", 8))
            y_percent = float(row.get("Y %", 12))
            width_percent = float(row.get("Width %", 30))
            height_percent = float(row.get("Height %", 6))
            requested_font_size = float(row.get("Font Size", 11))
            style = str(row.get("Style", "Box") or "Box")
        except (TypeError, ValueError):
            continue

        if page_index < 0 or page_index >= len(doc):
            continue

        page = doc.load_page(page_index)
        x0 = max(0, min(100, x_percent)) / 100 * page.rect.width
        y0 = max(0, min(100, y_percent)) / 100 * page.rect.height
        width = max(1, min(100, width_percent)) / 100 * page.rect.width
        height = max(0.5, min(100, height_percent)) / 100 * page.rect.height
        x1 = min(page.rect.width, x0 + width)
        y1 = min(page.rect.height, y0 + height)
        rect = fitz.Rect(x0, y0, x1, y1)

        if style == "Highlight Box":
            page.draw_rect(rect, color=(0, 0, 0), fill=(1, 1, 0.65), width=0.7)
        elif style == "Box":
            page.draw_rect(rect, color=(0, 0, 0), fill=(1, 1, 1), width=0.7)

        horizontal_padding = min(2.0, max(0.7, rect.width * 0.02))
        vertical_padding = min(1.2, max(0.4, rect.height * 0.08))
        available_width = max(1.0, rect.width - (horizontal_padding * 2))
        available_height = max(1.0, rect.height - (vertical_padding * 2))

        font_size = min(requested_font_size, max(4.5, available_height * 0.78))
        text_width = fitz.get_text_length(label_text, fontname="helv", fontsize=font_size)
        if text_width > available_width and text_width > 0:
            font_size = max(4.5, font_size * (available_width / text_width))

        # Vertically center the one-line tag inside the rectangle.
        baseline = rect.y0 + ((rect.height - font_size) / 2) + (font_size * 0.82)
        page.insert_text(
            fitz.Point(rect.x0 + horizontal_padding, baseline),
            label_text,
            fontsize=font_size,
            fontname="helv",
            color=(0, 0, 0),
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
    """Read the persistent Components v2 editor state."""
    if state is None:
        return {"pages": {}, "selected_id": None, "active_page": 1, "updated_at": 0}
    if isinstance(state, dict):
        value = state.get("editor", {})
    else:
        value = getattr(state, "editor", {})
    return value if isinstance(value, dict) else {"pages": {}}


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



@st.cache_data(show_spinner=False)
def cached_archive_metadata(pdf_bytes: bytes, filename: str):
    return extract_archive_metadata(pdf_bytes, filename)


@st.cache_resource(show_spinner=False)
def cached_archive_client(url: str, service_role_key: str, bucket: str, table: str):
    return create_archive_client(
        ArchiveConfig(
            url=url,
            service_role_key=service_role_key,
            bucket=bucket,
            table=table,
        )
    )


def archive_client_or_none(config: ArchiveConfig):
    if not archive_is_configured(config):
        return None
    try:
        return cached_archive_client(
            config.url,
            config.service_role_key,
            config.bucket,
            config.table,
        )
    except Exception:
        return None


def archive_access_granted(config: ArchiveConfig) -> bool:
    if not archive_is_configured(config):
        return False
    if not config.access_pin:
        return False
    return bool(st.session_state.get("archive_access_granted", False))


def render_archive_setup_notice():
    st.warning("Permanent PDF archiving is not configured yet.")
    st.markdown(
        "1. Create a Supabase project.\n"
        "2. Run `SUPABASE_SETUP.sql` in the Supabase SQL Editor.\n"
        "3. Copy the values from `.streamlit/secrets.toml.example` into Streamlit **App settings > Secrets**.\n"
        "4. Use the **service-role key** only in Streamlit Secrets. Never commit it to GitHub."
    )
    st.code(
        '[supabase]\n'
        'url = "https://YOUR-PROJECT.supabase.co"\n'
        'service_role_key = "YOUR-SERVICE-ROLE-KEY"\n'
        'bucket = "audit-pdf-archive"\n'
        'table = "pdf_archive"\n\n'
        '[archive]\n'
        'access_pin = "YOUR-STRONG-INTERNAL-PIN"',
        language="toml",
    )


def render_archive_login(config: ArchiveConfig) -> bool:
    if not archive_is_configured(config):
        render_archive_setup_notice()
        return False
    if not config.access_pin:
        st.error("Set `[archive].access_pin` in Streamlit Secrets before opening the PDF archive.")
        return False
    if st.session_state.get("archive_access_granted", False):
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.success("Saved PDFs archive is unlocked for this browser session.")
        with col_b:
            if st.button("Lock Archive"):
                st.session_state["archive_access_granted"] = False
                st.rerun()
        return True

    pin = st.text_input("Archive access PIN", type="password", key="archive_pin_input")
    if st.button("Unlock Saved PDFs", type="primary"):
        if pin == config.access_pin:
            st.session_state["archive_access_granted"] = True
            st.rerun()
        else:
            st.error("Incorrect archive PIN.")
    return False


def archive_pdf_with_feedback(
    client,
    config: ArchiveConfig,
    *,
    pdf_bytes: bytes,
    filename: str,
    audit_reference: str,
    auditee_name: str,
    document_type: str,
    uploaded_by: str,
):
    try:
        record = upload_archived_pdf(
            client,
            config,
            pdf_bytes=pdf_bytes,
            original_filename=filename,
            audit_reference=audit_reference,
            auditee_name=auditee_name,
            document_type=document_type,
            uploaded_by=uploaded_by,
        )
        return {"Status": "Archived", "File": filename, "Details": record.get("storage_path", "")}
    except DuplicateArchiveError as exc:
        return {"Status": "Duplicate skipped", "File": filename, "Details": str(exc)}
    except Exception as exc:
        return {"Status": "Archive failed", "File": filename, "Details": str(exc)}


archive_config = read_archive_config(st.secrets)
archive_client = archive_client_or_none(archive_config)
archive_ready = archive_is_configured(archive_config) and archive_client is not None
archive_unlocked = archive_access_granted(archive_config)

st.title("Internal Audit Report System (IARS)")
st.caption("Permanent Master Data + Multiple PDF extraction + PDF Textbox Editor + Private PDF Archive v3.0")

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
    st.header("PDF Archive")
    if archive_ready:
        st.success("Supabase private archive connected.")
        st.caption(f"Bucket: {archive_config.bucket}")
        if archive_unlocked:
            st.caption("Access: Unlocked")
        else:
            st.caption("Access: Locked")
    else:
        st.warning("Supabase archive not configured.")

if not MASTER_DATA_PATH.exists():
    st.info("Please upload or add data/Master_Data.xlsx before generating extraction.")
    st.stop()

master_df, master_sheets = load_master_data(str(MASTER_DATA_PATH))
auditors_df = master_sheets.get("Auditors", pd.DataFrame())
auditor_options = auditors_df["Auditor"].dropna().astype(str).tolist() if not auditors_df.empty and "Auditor" in auditors_df.columns else AUDITORS

tab_extract, tab_editor, tab_archive = st.tabs(["Generate Extraction", "PDF Tagging Editor", "Saved PDFs"])


with tab_editor:
    st.subheader("PDF Tagging Editor")
    st.caption(
        "Double-right-click the PDF to add a textbox. Click inside to type, "
        "drag the move tab to reposition, and drag the blue handles to resize. "
        "Tags are preserved when switching PDF pages."
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
            reset_key = f"pdf_editor_reset_{file_id}"
            reset_version = int(st.session_state.get(reset_key, 0))
            component_key = f"iars_pdf_editor_{file_id}_v24_reset_{reset_version}"
            storage_key = f"iars_pdf_editor_{file_id}_v24_reset_{reset_version}"

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
                    "The first right-click marks the location. Right-click the same spot again "
                    "to create a textbox. Use Fit text for the tightest box around the label."
                )

            preview_img, page_width, page_height = render_pdf_page(
                pdf_bytes,
                int(preview_page) - 1,
                zoom=1.7,
            )

            if preview_img is None:
                st.error("Unable to render this PDF page.")
                current_editor = component_editor_value(st.session_state.get(component_key))
            else:
                editor_result = pdf_textbox_editor(
                    image_data=image_to_data_uri(preview_img),
                    page_number=int(preview_page),
                    storage_key=storage_key,
                    key=component_key,
                    height=940,
                )

                current_editor = component_editor_value(editor_result)
                pages = current_editor.get("pages", {})
                boxes = pages.get(str(int(preview_page)), []) if isinstance(pages, dict) else []
                nonempty_boxes = [box for box in boxes if str(box.get("text", "")).strip()]
                st.caption(
                    f"Page {int(preview_page)}: {len(boxes)} textbox(es), "
                    f"{len(nonempty_boxes)} containing text."
                )

            if not current_editor.get("pages"):
                current_editor = component_editor_value(st.session_state.get(component_key))
            all_pages = current_editor.get("pages", {}) if isinstance(current_editor, dict) else {}

            all_tag_rows = []
            if isinstance(all_pages, dict):
                for page_number_text, page_boxes in all_pages.items():
                    try:
                        page_number = int(page_number_text)
                    except (TypeError, ValueError):
                        continue
                    if page_number < 1 or page_number > page_count or not isinstance(page_boxes, list):
                        continue
                    for box in page_boxes:
                        label_text = " ".join(str(box.get("text", "") or "").split())
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

            all_tag_rows.sort(key=lambda row: (row["Page"], row["Y %"], row["X %"]))

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
                    st.session_state[reset_key] = reset_version + 1
                    st.session_state.pop(component_key, None)
                    st.session_state.pop(f"tagged_pdf_{file_id}", None)
                    st.rerun()

            with st.expander("Save original/tagged PDF to permanent archive"):
                if not archive_ready:
                    render_archive_setup_notice()
                elif not archive_unlocked:
                    st.info("Unlock the archive in the Saved PDFs tab before saving files.")
                else:
                    archive_defaults = cached_archive_metadata(pdf_bytes, tag_pdf.name)
                    ar_ref = st.text_input(
                        "Audit Reference",
                        value=archive_defaults.get("audit_reference", ""),
                        key=f"tag_archive_ref_{file_id}",
                    )
                    ar_name = st.text_input(
                        "Auditee Name",
                        value=archive_defaults.get("auditee_name", ""),
                        key=f"tag_archive_name_{file_id}",
                    )
                    ar_by = st.text_input("Uploaded By", key=f"tag_archive_by_{file_id}")
                    ar_versions = st.multiselect(
                        "PDF version to archive",
                        ["Original", "Tagged"],
                        default=["Original"] + (["Tagged"] if st.session_state.get(f"tagged_pdf_{file_id}") else []),
                        key=f"tag_archive_versions_{file_id}",
                    )
                    if st.button("Save Selected PDF Version(s)", key=f"tag_archive_save_{file_id}"):
                        if not ar_by.strip():
                            st.error("Uploaded By is required.")
                        elif not ar_versions:
                            st.error("Select at least one PDF version.")
                        else:
                            archive_results = []
                            if "Original" in ar_versions:
                                archive_results.append(
                                    archive_pdf_with_feedback(
                                        archive_client,
                                        archive_config,
                                        pdf_bytes=pdf_bytes,
                                        filename=tag_pdf.name,
                                        audit_reference=ar_ref,
                                        auditee_name=ar_name,
                                        document_type="Original",
                                        uploaded_by=ar_by,
                                    )
                                )
                            if "Tagged" in ar_versions:
                                tagged_data = st.session_state.get(f"tagged_pdf_{file_id}")
                                if tagged_data:
                                    archive_results.append(
                                        archive_pdf_with_feedback(
                                            archive_client,
                                            archive_config,
                                            pdf_bytes=tagged_data,
                                            filename=f"tagged_{tag_pdf.name}",
                                            audit_reference=ar_ref,
                                            auditee_name=ar_name,
                                            document_type="Tagged",
                                            uploaded_by=ar_by,
                                        )
                                    )
                                else:
                                    archive_results.append({"Status": "Skipped", "File": f"tagged_{tag_pdf.name}", "Details": "Generate the tagged PDF first."})
                            st.dataframe(pd.DataFrame(archive_results), width="stretch", hide_index=True)
    else:
        st.info("Upload a PDF only when tags are needed. Otherwise, use Generate Extraction directly.")


with tab_archive:
    st.subheader("Saved PDFs")
    st.caption("Private permanent archive for original and tagged audit-report PDFs.")

    if render_archive_login(archive_config):
        archive_unlocked = True
        archive_client = archive_client_or_none(archive_config)
        if archive_client is None:
            st.error("Unable to connect to Supabase. Verify the URL and service-role key in Streamlit Secrets.")
        else:
            st.markdown("### Upload PDFs to Archive")
            saved_uploads = st.file_uploader(
                "Select one or multiple PDF files",
                type=["pdf"],
                accept_multiple_files=True,
                key="archive_direct_upload",
            )
            direct_uploaded_by = st.text_input("Uploaded By", key="archive_direct_uploaded_by")

            prepared_entries = []
            if saved_uploads:
                for index, uploaded in enumerate(saved_uploads):
                    data = uploaded.getvalue()
                    defaults = cached_archive_metadata(data, uploaded.name)
                    with st.expander(uploaded.name, expanded=len(saved_uploads) == 1):
                        ref = st.text_input(
                            "Audit Reference",
                            value=defaults.get("audit_reference", ""),
                            key=f"archive_ref_{index}_{uploaded.name}",
                        )
                        auditee = st.text_input(
                            "Auditee Name",
                            value=defaults.get("auditee_name", ""),
                            key=f"archive_auditee_{index}_{uploaded.name}",
                        )
                        doc_type = st.selectbox(
                            "Document Type",
                            ["Original", "Tagged"],
                            key=f"archive_type_{index}_{uploaded.name}",
                        )
                    prepared_entries.append((uploaded.name, data, ref, auditee, doc_type))

                if st.button("Archive Selected PDFs", type="primary"):
                    if not direct_uploaded_by.strip():
                        st.error("Uploaded By is required.")
                    else:
                        results = []
                        for filename, data, ref, auditee, doc_type in prepared_entries:
                            results.append(
                                archive_pdf_with_feedback(
                                    archive_client,
                                    archive_config,
                                    pdf_bytes=data,
                                    filename=filename,
                                    audit_reference=ref,
                                    auditee_name=auditee,
                                    document_type=doc_type,
                                    uploaded_by=direct_uploaded_by,
                                )
                            )
                        st.dataframe(pd.DataFrame(results), width="stretch", hide_index=True)

            st.divider()
            title_col, refresh_col = st.columns([4, 1])
            with title_col:
                st.markdown("### Archived PDF Records")
            with refresh_col:
                if st.button("Refresh List"):
                    st.session_state.pop("archive_preview_bytes", None)
                    st.rerun()

            try:
                records = list_archive_records(archive_client, archive_config)
            except Exception as exc:
                st.error(f"Unable to load archive records: {exc}")
                records = []

            if not records:
                st.info("No PDFs have been archived yet.")
            else:
                filter_1, filter_2, filter_3, filter_4 = st.columns([2, 1, 1, 1])
                with filter_1:
                    search_text = st.text_input(
                        "Search",
                        placeholder="Audit reference, auditee, filename or uploader",
                        key="archive_search",
                    )
                with filter_2:
                    type_filter = st.selectbox("Document Type", ["All", "Original", "Tagged"], key="archive_type_filter")
                with filter_3:
                    start_filter = st.date_input("Uploaded From", value=None, key="archive_start_date")
                with filter_4:
                    end_filter = st.date_input("Uploaded To", value=None, key="archive_end_date")

                filtered = filter_archive_records(
                    records,
                    search=search_text,
                    document_type=type_filter,
                    start_date=start_filter if isinstance(start_filter, date) else None,
                    end_date=end_filter if isinstance(end_filter, date) else None,
                )

                display_rows = []
                for record in filtered:
                    display_rows.append(
                        {
                            "Audit Reference": record.get("audit_reference", ""),
                            "Auditee Name": record.get("auditee_name", ""),
                            "Filename": record.get("original_filename", ""),
                            "Type": record.get("document_type", ""),
                            "Uploaded Date": str(record.get("uploaded_at", ""))[:10],
                            "Uploaded By": record.get("uploaded_by", ""),
                            "File Size": human_file_size(record.get("file_size")),
                        }
                    )

                st.caption(f"Showing {len(filtered)} of {len(records)} archived PDF record(s).")
                if display_rows:
                    st.dataframe(pd.DataFrame(display_rows), width="stretch", hide_index=True)

                    labels = []
                    record_by_label = {}
                    for idx, record in enumerate(filtered, start=1):
                        label = (
                            f"{record.get('audit_reference') or 'No Ref'} | "
                            f"{record.get('auditee_name') or 'No Auditee'} | "
                            f"{record.get('document_type', '')} | "
                            f"{record.get('original_filename', '')} | {idx}"
                        )
                        labels.append(label)
                        record_by_label[label] = record

                    selected_label = st.selectbox("Select a PDF to preview, download or delete", labels)
                    selected_record = record_by_label[selected_label]

                    if st.button("Load Selected PDF"):
                        try:
                            selected_bytes = download_archived_pdf(
                                archive_client,
                                archive_config,
                                selected_record.get("storage_path", ""),
                            )
                            st.session_state["archive_preview_bytes"] = selected_bytes
                            st.session_state["archive_preview_record_id"] = selected_record.get("id")
                        except Exception as exc:
                            st.error(str(exc))

                    selected_bytes = None
                    if st.session_state.get("archive_preview_record_id") == selected_record.get("id"):
                        selected_bytes = st.session_state.get("archive_preview_bytes")

                    if selected_bytes:
                        st.download_button(
                            "Download Selected PDF",
                            data=selected_bytes,
                            file_name=selected_record.get("original_filename", "archived.pdf"),
                            mime="application/pdf",
                        )
                        try:
                            import fitz

                            archive_doc = fitz.open(stream=selected_bytes, filetype="pdf")
                            preview_page = st.number_input(
                                "Preview Page",
                                min_value=1,
                                max_value=len(archive_doc),
                                value=1,
                                step=1,
                                key=f"archive_preview_page_{selected_record.get('id')}",
                            )
                            preview_image, _, _ = render_pdf_page(selected_bytes, int(preview_page) - 1, zoom=1.35)
                            if preview_image is not None:
                                st.image(preview_image, caption=f"Page {preview_page}", width="stretch")
                        except Exception as exc:
                            st.warning(f"PDF preview unavailable: {exc}")

                    st.markdown("#### Delete Selected PDF")
                    st.warning("Deleting removes both the private Storage object and its archive metadata.")
                    confirmation = st.text_input(
                        "Type DELETE to confirm",
                        key=f"delete_confirm_{selected_record.get('id')}",
                    )
                    if st.button(
                        "Delete Selected PDF",
                        type="primary",
                        disabled=confirmation.strip().upper() != "DELETE",
                    ):
                        try:
                            delete_archived_pdf(archive_client, archive_config, selected_record)
                            st.session_state.pop("archive_preview_bytes", None)
                            st.session_state.pop("archive_preview_record_id", None)
                            st.success("Archived PDF deleted successfully.")
                            st.rerun()
                        except Exception as exc:
                            st.error(str(exc))
                else:
                    st.info("No archived PDFs match the selected filters.")


with tab_extract:
    st.subheader("System Status")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Master Data", "Loaded")
    with col2:
        st.metric("Employees", len(master_df))
    with col3:
        st.metric("PDF Archive", "Connected" if archive_ready else "Not configured")

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

        archive_after_extract = False
        extraction_uploaded_by = ""
        if archive_ready and archive_unlocked:
            archive_after_extract = st.checkbox(
                "Save successfully processed original PDFs to the permanent archive",
                value=True,
                key="archive_after_extract",
            )
            if archive_after_extract:
                extraction_uploaded_by = st.text_input("Uploaded By", key="extract_archive_uploaded_by")
        elif archive_ready:
            st.info("Unlock the Saved PDFs tab to enable automatic archiving after extraction.")
        else:
            st.caption("Permanent archive is unavailable until Supabase is configured.")

        if st.button("Generate Extraction", type="primary"):
            all_results = []
            processing_errors = []
            archive_results = []

            if archive_after_extract and not extraction_uploaded_by.strip():
                st.error("Uploaded By is required when automatic archiving is enabled.")
                st.stop()

            progress = st.progress(0)
            status = st.empty()

            for idx, pdf_file in enumerate(pdf_files, start=1):
                pdf_data = pdf_file.getvalue()
                try:
                    status.write(f"Processing {idx} of {len(pdf_files)}: {pdf_file.name}")
                    pdf_file.seek(0)
                    result_df, header, items = build_records(pdf_file, master_df, auditors_df=auditors_df)
                    all_results.append(result_df)

                    if archive_after_extract:
                        archive_results.append(
                            archive_pdf_with_feedback(
                                archive_client,
                                archive_config,
                                pdf_bytes=pdf_data,
                                filename=pdf_file.name,
                                audit_reference=str(header.get("audit_reference", "") or ""),
                                auditee_name=str(header.get("auditee_name", "") or ""),
                                document_type="Original",
                                uploaded_by=extraction_uploaded_by,
                            )
                        )

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

            if archive_results:
                st.subheader("Archive Results")
                st.dataframe(pd.DataFrame(archive_results), width="stretch", hide_index=True)

            if processing_errors:
                st.warning("Some PDF files were not processed.")
                st.dataframe(pd.DataFrame(processing_errors), width="stretch")

    else:
        st.info("Upload one or multiple audit report PDFs to start.")
