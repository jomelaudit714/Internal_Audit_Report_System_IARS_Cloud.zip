# Internal Audit Report System (IARS) v3.0

## New: Permanent Private PDF Archive

Version 3.0 preserves all existing extraction, tagging, Master Data, frequency, auditee-matching, explanation and date-format rules from v2.9 and adds a permanent PDF archive using **Supabase Storage + Supabase Postgres metadata**.

### Saved PDFs features

- Private `audit-pdf-archive` bucket
- Metadata table `pdf_archive`
- Archive original PDFs after successful extraction
- Archive original and/or tagged PDFs from the PDF Tagging Editor
- Direct multi-PDF archive upload
- Automatic detection of Audit Reference and Auditee Name
- Editable metadata before upload
- Search by Audit Reference, Auditee Name, filename or uploader
- Filter by Original/Tagged and upload-date range
- Newest-first records
- PDF preview with page navigation
- Download selected archived PDF
- Duplicate prevention through SHA-256
- Delete confirmation requiring `DELETE`
- Deletes both the Storage object and metadata row
- Archive access PIN stored only in Streamlit Secrets

## One-time Supabase setup

1. Create a Supabase project.
2. Open **SQL Editor** in Supabase.
3. Run the complete `SUPABASE_SETUP.sql` file.
4. In Streamlit Community Cloud, open **Manage app > Settings > Secrets**.
5. Paste and complete this configuration:

```toml
[supabase]
url = "https://YOUR-PROJECT.supabase.co"
service_role_key = "YOUR-SERVICE-ROLE-KEY"
bucket = "audit-pdf-archive"
table = "pdf_archive"

[archive]
access_pin = "YOUR-STRONG-INTERNAL-PIN"
```

The same template is included as `.streamlit/secrets.toml.example`.

## Security requirements

- Never upload `.streamlit/secrets.toml` to GitHub.
- Never place the Supabase service-role key directly in `app.py`.
- The service-role key bypasses Row Level Security and must remain server-side.
- The bucket is private and the metadata table has Row Level Security enabled.
- No public Storage or database policies are created by the setup script.
- Use a strong Archive PIN because audit PDFs may contain confidential information.

## Normal workflow

### Generate Extraction

1. Upload one or several audit PDFs.
2. Unlock **Saved PDFs** using the Archive PIN.
3. Keep **Save successfully processed original PDFs to the permanent archive** checked.
4. Enter `Uploaded By`.
5. Generate extraction.
6. Successfully processed originals are archived automatically. Duplicate files are skipped without blocking extraction.

### PDF Tagging Editor

1. Upload and tag the PDF.
2. Generate the tagged PDF.
3. Open **Save original/tagged PDF to permanent archive**.
4. Select `Original`, `Tagged`, or both.
5. Enter `Uploaded By` and save.

### Saved PDFs

1. Unlock with the Archive PIN.
2. Upload files directly or review existing records.
3. Search/filter the archive.
4. Select a record and click **Load Selected PDF**.
5. Preview or download it.
6. To delete, type `DELETE` and click **Delete Selected PDF**.

## Repository files

- `app.py` - Streamlit interface
- `iars_parser.py` - audit extraction rules
- `iars_pdf_editor.py` - PDF textbox editor
- `iars_archive.py` - Supabase archive operations
- `data/Master_Data.xlsx` - current permanent Master Data
- `SUPABASE_SETUP.sql` - one-time bucket/table setup
- `.streamlit/secrets.toml.example` - secrets template only
- `requirements.txt` - Python dependencies
- `packages.txt` - operating-system dependencies
- `TEST_RESULTS.md` - verification record

## Important limitation

The application and archive logic were locally tested using the current source files and a simulated Supabase client. A live Supabase upload/download/delete test requires your own Supabase project and credentials. The app remains fully usable for extraction and PDF tagging before Supabase is configured; the Saved PDFs tab displays setup instructions until valid secrets are supplied.
