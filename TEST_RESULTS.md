# IARS v3.0 Test Results

Test date: 2026-06-22

## Application tests

- Python compilation: PASS
  - `app.py`
  - `iars_archive.py`
  - `iars_parser.py`
  - `iars_pdf_editor.py`
- Streamlit 1.58.0 AppTest with archive secrets absent: PASS
- AppTest exceptions: 0
- Tabs detected:
  - Generate Extraction
  - PDF Tagging Editor
  - Saved PDFs
- Local Streamlit server startup: PASS
- Streamlit health endpoint: PASS

## Archive service tests using simulated Supabase

- Upload PDF to private bucket abstraction: PASS
- Insert archive metadata: PASS
- SHA-256 duplicate prevention: PASS
- Newest-first record listing: PASS
- Search/filter by auditee, type and date: PASS
- Private PDF download: PASS
- Delete Storage object: PASS
- Delete metadata row: PASS
- Storage path sanitization: PASS
- Year/Audit Reference/Original-Tagged folder structure: PASS

## Real PDF metadata test

Source: `tagged_2026IAD222_Vet_City_Marikina (2).pdf`

- Audit Reference detected: `2026IAD222` - PASS
- Header Auditee detected: `Dianne Susie Berbano and Jinky Venise Angel` - PASS

## Parser regression test

The current 2026IAD222 tagged PDF was processed using the included Master Data.

- Finding rows: 7 - PASS
- `#` column blank: PASS
- Encoded Date format `yyyy-mm-dd`: PASS
- Date Reported: `2026-06-09` - PASS
- True issue-title rules retained: PASS
- PCV missing-detail augmentation retained: PASS
- Issue-specific frequency retained: PASS
- Second Time -> Performed SAME offense retained: PASS
- First-name auditee matching retained: PASS

## Dependency/API compatibility checks

- `supabase==2.31.0` installed and imported: PASS
- Storage upload accepts `bytes`: PASS
- Storage download returns `bytes`: PASS
- Storage remove accepts `list[str]`: PASS

## Live-cloud limitation

A real Supabase project was not available during packaging. Therefore, live network upload, list, download and delete operations could not be executed against the user's production project. The same operations were tested using a stateful simulated Supabase client, and the Python method signatures were checked against `supabase==2.31.0`.
