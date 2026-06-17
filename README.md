# Internal Audit Report System (IARS) v1.1

## Changes in v1.1
- Master Data is stored permanently in `data/Master_Data.xlsx`.
- Users no longer need to upload Master Data for every report.
- Multiple audit report PDFs can be uploaded and processed at once.
- Output is consolidated into one Excel file.
- `Source PDF` column is added for traceability.

## Files
- `app.py` - Streamlit interface
- `iars_parser.py` - PDF parser and extraction logic
- `requirements.txt` - Python dependencies
- `data/Master_Data.xlsx` - permanent Master Data file

## How to update Master Data permanently
Replace this file in GitHub:

`data/Master_Data.xlsx`

Then commit changes and wait for Streamlit to redeploy.


## OCR / Scanned PDF Support

This version includes OCR fallback for scanned/image PDFs. On Streamlit Cloud, keep `packages.txt` in the repository so `tesseract-ocr` is installed.

Supported handwritten/typed carry-forward tags:
- `Auditee: <name>`
- `Auditor: <name>`
- `Task ID: <id>`
- `Frequency Rate: <value>`
- `Reaction: <value>`

A tag applies to succeeding issue rows until another tag of the same type appears.

For best OCR accuracy, write tags clearly using colon format, e.g. `Task ID: 001`, `Auditor: Sarina Amuraw`, `Auditee: Emerito Bondoc`.


## Multiple Auditee Priority Rule

For scanned/OCR reports, if an auditee name is written/printed above the issue title, that auditee is applied to that issue and all following issues until another auditee name is detected above a later issue title. Auditor, Task ID, Frequency Rate, and Reaction handwritten tags continue to use their own carry-forward rules.
