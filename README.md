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
