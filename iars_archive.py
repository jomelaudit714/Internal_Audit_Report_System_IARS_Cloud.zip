from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import re
from typing import Any, Iterable

from iars_parser import extract_all_text, extract_header

DEFAULT_BUCKET = "audit-pdf-archive"
DEFAULT_TABLE = "pdf_archive"
DEFAULT_AUDITORS_TABLE = "auditors_master"


class ArchiveError(RuntimeError):
    """Base exception for PDF archive operations."""


class ArchiveNotConfiguredError(ArchiveError):
    """Raised when required Supabase settings are absent."""


class DuplicateArchiveError(ArchiveError):
    """Raised when an identical PDF is already archived."""

    def __init__(self, message: str, existing: dict[str, Any] | None = None):
        super().__init__(message)
        self.existing = existing or {}


@dataclass(frozen=True)
class ArchiveConfig:
    url: str
    service_role_key: str
    bucket: str = DEFAULT_BUCKET
    table: str = DEFAULT_TABLE
    access_pin: str = ""


def _secret_value(container: Any, key: str, default: str = "") -> str:
    try:
        value = container.get(key, default)
    except Exception:
        try:
            value = container[key]
        except Exception:
            value = default
    return str(value or "").strip()


def read_archive_config(secrets: Any) -> ArchiveConfig:
    """Read archive settings from Streamlit secrets.

    Preferred format:
        [supabase]
        url = "..."
        service_role_key = "..."
        bucket = "audit-pdf-archive"
        table = "pdf_archive"

        [archive]
        access_pin = "..."

    Flat keys are supported for backward compatibility.
    """
    supabase_section = {}
    archive_section = {}
    try:
        supabase_section = secrets.get("supabase", {})
        archive_section = secrets.get("archive", {})
    except Exception:
        pass

    url = (
        _secret_value(supabase_section, "url")
        or _secret_value(secrets, "SUPABASE_URL")
    )
    key = (
        _secret_value(supabase_section, "service_role_key")
        or _secret_value(supabase_section, "key")
        or _secret_value(secrets, "SUPABASE_SERVICE_ROLE_KEY")
        or _secret_value(secrets, "SUPABASE_KEY")
    )
    bucket = (
        _secret_value(supabase_section, "bucket")
        or _secret_value(secrets, "SUPABASE_BUCKET")
        or DEFAULT_BUCKET
    )
    table = (
        _secret_value(supabase_section, "table")
        or _secret_value(secrets, "SUPABASE_ARCHIVE_TABLE")
        or DEFAULT_TABLE
    )
    access_pin = (
        _secret_value(archive_section, "access_pin")
        or _secret_value(secrets, "ARCHIVE_ACCESS_PIN")
    )

    return ArchiveConfig(
        url=url,
        service_role_key=key,
        bucket=bucket,
        table=table,
        access_pin=access_pin,
    )


def archive_is_configured(config: ArchiveConfig) -> bool:
    return bool(config.url and config.service_role_key and config.bucket and config.table)


def create_archive_client(config: ArchiveConfig):
    if not archive_is_configured(config):
        raise ArchiveNotConfiguredError(
            "Supabase archive is not configured. Add the Supabase URL and service-role key to Streamlit Secrets."
        )
    try:
        from supabase import create_client
    except Exception as exc:  # pragma: no cover - deployment guard
        raise ArchiveNotConfiguredError(
            "The supabase Python package is not installed."
        ) from exc
    return create_client(config.url, config.service_role_key)


def sanitize_segment(value: str, fallback: str = "unknown") -> str:
    value = str(value or "").strip()
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("._-")
    return value[:120] or fallback


def normalize_document_type(value: str) -> str:
    normalized = str(value or "Original").strip().lower()
    if normalized in {"tagged", "tagged pdf"}:
        return "Tagged"
    return "Original"


def make_storage_path(
    audit_reference: str,
    original_filename: str,
    document_type: str,
    now: datetime | None = None,
) -> str:
    now = now or datetime.now(timezone.utc)
    ref = sanitize_segment(audit_reference, "UNASSIGNED")
    year_match = re.search(r"\b(20\d{2})\b", audit_reference or "")
    year = year_match.group(1) if year_match else str(now.year)
    filename = sanitize_segment(Path(original_filename).name, "document.pdf")
    if not filename.lower().endswith(".pdf"):
        filename += ".pdf"
    doc_type = normalize_document_type(document_type).lower()
    timestamp = now.strftime("%Y%m%dT%H%M%S%fZ")
    return f"{year}/{ref}/{doc_type}/{timestamp}_{filename}"


def pdf_hash(pdf_bytes: bytes) -> str:
    return sha256(pdf_bytes).hexdigest()


def compress_pdf_for_archive(pdf_bytes: bytes) -> tuple[bytes, dict[str, Any]]:
    """Return a smaller archive-ready PDF when safe and beneficial.

    The routine keeps searchable text and PDF structure intact. It first
    recompresses oversized images using balanced settings, then performs
    lossless object/font/stream optimization. If optimization fails, if the
    PDF is encrypted or digitally signed, or if the result is not smaller,
    the original bytes are retained so archiving is never blocked.
    """
    original_size = len(pdf_bytes or b"")
    result = {
        "original_size": original_size,
        "stored_size": original_size,
        "saved_bytes": 0,
        "reduction_percent": 0.0,
        "compression_applied": False,
        "compression_note": "Original retained",
    }

    if not pdf_bytes:
        return pdf_bytes, result

    try:
        import fitz

        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            if getattr(document, "needs_pass", False):
                result["compression_note"] = "Encrypted PDF retained without modification"
                return pdf_bytes, result

            try:
                signature_flags = int(document.get_sigflags())
            except Exception:
                signature_flags = -1
            if signature_flags > 0:
                result["compression_note"] = "Digitally signed PDF retained to protect the signature"
                return pdf_bytes, result

            # Balanced image recompression: only images above 220 DPI are
            # downsampled, to 150 DPI at JPEG quality 72. Text remains text.
            rewrite_images = getattr(document, "rewrite_images", None)
            if callable(rewrite_images):
                try:
                    rewrite_images(
                        dpi_threshold=220,
                        dpi_target=150,
                        quality=72,
                        lossy=True,
                        lossless=True,
                        bitonal=True,
                        color=True,
                        gray=True,
                        set_to_gray=False,
                    )
                except Exception:
                    # Continue with lossless PDF optimization even when a
                    # particular image cannot be rewritten.
                    pass

            output = BytesIO()
            document.save(
                output,
                garbage=4,
                clean=True,
                deflate=True,
                deflate_images=True,
                deflate_fonts=True,
                use_objstms=1,
                compression_effort=60,
            )
            candidate = output.getvalue()
        finally:
            document.close()

        if candidate and len(candidate) < original_size:
            stored_size = len(candidate)
            saved_bytes = original_size - stored_size
            result.update(
                {
                    "stored_size": stored_size,
                    "saved_bytes": saved_bytes,
                    "reduction_percent": round((saved_bytes / original_size) * 100, 1),
                    "compression_applied": True,
                    "compression_note": "Compressed automatically before archive upload",
                }
            )
            return candidate, result

        result["compression_note"] = "PDF was already optimized; original retained"
        return pdf_bytes, result
    except Exception as exc:
        # Compression is a best-effort archive optimization. The upload must
        # still proceed using the original PDF if optimization is unavailable.
        result["compression_note"] = f"Compression skipped: {exc}"
        return pdf_bytes, result


def extract_archive_metadata(pdf_bytes: bytes, filename: str = "") -> dict[str, str]:
    """Extract audit reference and auditee header from a PDF.

    Uses the same searchable-PDF/OCR extraction logic as the main parser.
    Returns editable defaults even when a field cannot be detected.
    """
    file_obj = BytesIO(pdf_bytes)
    file_obj.name = filename or "uploaded.pdf"
    try:
        text = extract_all_text(file_obj)
        header = extract_header(text)
    except Exception:
        header = {}

    audit_reference = str(header.get("audit_reference", "") or "").strip()
    auditee_name = str(header.get("auditee_name", "") or "").strip()
    invalid_values = {"none", "n/a", "not found", ""}
    if audit_reference.lower() in invalid_values:
        audit_reference = ""
    if auditee_name.lower() in invalid_values:
        auditee_name = ""

    return {
        "audit_reference": audit_reference,
        "auditee_name": auditee_name,
    }


def _response_data(response: Any) -> list[dict[str, Any]]:
    data = getattr(response, "data", None)
    if data is None and isinstance(response, dict):
        data = response.get("data")
    if data is None:
        return []
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def find_duplicate(client: Any, config: ArchiveConfig, digest: str) -> dict[str, Any] | None:
    response = (
        client.table(config.table)
        .select("id,audit_reference,auditee_name,original_filename,storage_path,document_type,uploaded_at,uploaded_by,file_size,sha256")
        .eq("sha256", digest)
        .limit(1)
        .execute()
    )
    rows = _response_data(response)
    return rows[0] if rows else None


def upload_pdf(
    client: Any,
    config: ArchiveConfig,
    *,
    pdf_bytes: bytes,
    original_filename: str,
    audit_reference: str,
    auditee_name: str,
    document_type: str,
    uploaded_by: str,
    prevent_duplicate: bool = True,
) -> dict[str, Any]:
    if not pdf_bytes:
        raise ArchiveError("The PDF is empty.")
    if not str(original_filename or "").lower().endswith(".pdf"):
        raise ArchiveError("Only PDF files can be archived.")

    # Duplicate detection uses the original uploaded bytes, so the same PDF
    # remains detectable even though the stored copy is compressed.
    digest = pdf_hash(pdf_bytes)
    if prevent_duplicate:
        existing = find_duplicate(client, config, digest)
        if existing:
            raise DuplicateArchiveError(
                f"This exact PDF is already archived as {existing.get('original_filename', 'an existing file')}.",
                existing,
            )

    stored_pdf_bytes, compression = compress_pdf_for_archive(pdf_bytes)

    doc_type = normalize_document_type(document_type)
    storage_path = make_storage_path(
        audit_reference=audit_reference,
        original_filename=original_filename,
        document_type=doc_type,
    )

    bucket = client.storage.from_(config.bucket)
    try:
        bucket.upload(
            path=storage_path,
            file=stored_pdf_bytes,
            file_options={
                "content-type": "application/pdf",
                "cache-control": "3600",
                "upsert": "false",
            },
        )
    except Exception as exc:
        raise ArchiveError(f"Unable to upload PDF to Supabase Storage: {exc}") from exc

    metadata = {
        "audit_reference": str(audit_reference or "").strip(),
        "auditee_name": str(auditee_name or "").strip(),
        "original_filename": Path(original_filename).name,
        "storage_bucket": config.bucket,
        "storage_path": storage_path,
        "document_type": doc_type,
        "uploaded_by": str(uploaded_by or "").strip(),
        "file_size": len(stored_pdf_bytes),
        "sha256": digest,
    }

    try:
        response = client.table(config.table).insert(metadata).execute()
        rows = _response_data(response)
        record = dict(rows[0] if rows else metadata)
        # Transient feedback fields are returned to Streamlit only; they are
        # not inserted into Supabase and require no database migration.
        record["_compression"] = compression
        return record
    except Exception as exc:
        # Roll back the storage object if metadata insertion fails.
        try:
            bucket.remove([storage_path])
        except Exception:
            pass
        raise ArchiveError(f"PDF uploaded, but metadata could not be saved: {exc}") from exc


def list_records(client: Any, config: ArchiveConfig, limit: int = 1000) -> list[dict[str, Any]]:
    response = (
        client.table(config.table)
        .select("id,audit_reference,auditee_name,original_filename,storage_bucket,storage_path,document_type,uploaded_at,uploaded_by,file_size,sha256")
        .order("uploaded_at", desc=True)
        .limit(limit)
        .execute()
    )
    return _response_data(response)


def download_pdf(client: Any, config: ArchiveConfig, storage_path: str) -> bytes:
    try:
        data = client.storage.from_(config.bucket).download(storage_path)
    except Exception as exc:
        raise ArchiveError(f"Unable to download the archived PDF: {exc}") from exc
    if isinstance(data, bytes):
        return data
    if hasattr(data, "read"):
        return data.read()
    try:
        return bytes(data)
    except Exception as exc:
        raise ArchiveError("Supabase returned an unsupported download response.") from exc


def delete_pdf(client: Any, config: ArchiveConfig, record: dict[str, Any]) -> None:
    record_id = record.get("id")
    storage_path = str(record.get("storage_path", "") or "").strip()
    if not record_id or not storage_path:
        raise ArchiveError("The selected archive record is incomplete.")

    try:
        client.storage.from_(config.bucket).remove([storage_path])
    except Exception as exc:
        raise ArchiveError(f"Unable to delete the PDF from Storage: {exc}") from exc

    try:
        client.table(config.table).delete().eq("id", record_id).execute()
    except Exception as exc:
        raise ArchiveError(
            "The PDF was removed from Storage, but the metadata row could not be deleted. "
            f"Remove metadata record {record_id} manually. Details: {exc}"
        ) from exc


def filter_records(
    records: Iterable[dict[str, Any]],
    *,
    search: str = "",
    document_type: str = "All",
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict[str, Any]]:
    search_lower = str(search or "").strip().lower()
    wanted_type = str(document_type or "All").strip().lower()
    filtered: list[dict[str, Any]] = []

    for record in records:
        haystack = " ".join(
            str(record.get(key, "") or "")
            for key in ("audit_reference", "auditee_name", "original_filename", "uploaded_by")
        ).lower()
        if search_lower and search_lower not in haystack:
            continue

        record_type = str(record.get("document_type", "") or "").strip().lower()
        if wanted_type not in {"", "all"} and record_type != wanted_type:
            continue

        uploaded_at = str(record.get("uploaded_at", "") or "")
        uploaded_date = None
        if uploaded_at:
            try:
                uploaded_date = datetime.fromisoformat(uploaded_at.replace("Z", "+00:00")).date()
            except ValueError:
                pass
        if start_date and uploaded_date and uploaded_date < start_date:
            continue
        if end_date and uploaded_date and uploaded_date > end_date:
            continue

        filtered.append(record)

    return filtered


def human_file_size(size_bytes: Any) -> str:
    try:
        size = float(size_bytes)
    except (TypeError, ValueError):
        return ""
    units = ["B", "KB", "MB", "GB"]
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.0f} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return ""


def list_additional_auditors(
    client: Any,
    table: str = DEFAULT_AUDITORS_TABLE,
    *,
    active_only: bool = False,
) -> list[dict[str, Any]]:
    """Return auditors added through the IARS archive interface.

    Master Data remains the primary auditor source. This table stores only
    additional auditors that must persist across Streamlit restarts.
    """
    query = client.table(table).select(
        "id,auditor_name,designation,user_display,email,status,created_at,created_by"
    ).order("auditor_name")
    if active_only:
        query = query.eq("status", "Active")
    return _response_data(query.execute())


def add_additional_auditor(
    client: Any,
    *,
    auditor_name: str,
    designation: str = "",
    user_display: str = "",
    email: str = "",
    status: str = "Active",
    created_by: str = "IARS Admin",
    table: str = DEFAULT_AUDITORS_TABLE,
) -> dict[str, Any]:
    """Add a persistent auditor after case-insensitive duplicate checking."""
    name = " ".join(str(auditor_name or "").split()).strip()
    if not name:
        raise ArchiveError("Auditor Full Name is required.")

    status_value = str(status or "Active").strip().title()
    if status_value not in {"Active", "Inactive"}:
        raise ArchiveError("Auditor status must be Active or Inactive.")

    try:
        existing_rows = list_additional_auditors(client, table=table, active_only=False)
    except Exception as exc:
        raise ArchiveError(
            "Unable to access the additional-auditor table. Run "
            "SUPABASE_AUDITOR_MIGRATION.sql in Supabase first. "
            f"Details: {exc}"
        ) from exc

    normalized = name.casefold()
    for row in existing_rows:
        if " ".join(str(row.get("auditor_name", "") or "").split()).casefold() == normalized:
            raise ArchiveError(f"Auditor already exists: {row.get('auditor_name', name)}")

    payload = {
        "auditor_name": name,
        "designation": " ".join(str(designation or "").split()).strip(),
        "user_display": " ".join(str(user_display or "").split()).strip(),
        "email": str(email or "").strip(),
        "status": status_value,
        "created_by": " ".join(str(created_by or "IARS Admin").split()).strip() or "IARS Admin",
    }
    try:
        rows = _response_data(client.table(table).insert(payload).execute())
    except Exception as exc:
        raise ArchiveError(f"Unable to add the auditor: {exc}") from exc
    return rows[0] if rows else payload
