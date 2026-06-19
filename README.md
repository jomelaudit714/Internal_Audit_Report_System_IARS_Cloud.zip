# Internal Audit Report System (IARS) v2.5

## Main parser correction

Version 2.5 corrects Issue Detail Issue selection when an audit activity heading appears above the actual finding.

The following are treated only as audit activity/context headings and are never captured as the issue title:

- `REVOLVING FUND`
- `PETTY CASH FUND`
- `CASH ADVANCE` / `CASH ADVANCES`
- `SALES AND COLLECTION`
- `CASH SALES AND COLLECTION`
- `CHANGE FUND`
- `DELIVERY FUND`
- similar headings ending in `COUNT`

The parser now skips those headings and captures the next true issue title. It also removes merged PDF editor tags such as `Auditee:`, `Auditor:`, `Task ID:`, `Frequency Rate:`, and `Reaction:` from title detection.

### Confirmed example

For Report `2026IAD222`, the first finding is now extracted as:

- **Issue Detail Issue:** `CASH OVERAGE – P10,996.31`
- **Finding Category:** `Cash/Fund/Collection Overage (₱1,000.00 and above) -4`

It no longer captures `REVOLVING FUND` as the issue.

## PDF textbox editor

The Version 2.4 component-registration, page persistence, direct typing, drag repositioning, resizing, and tight textbox spacing fixes are retained.

- Double-right-click the same PDF location to add a textbox.
- Click inside the textbox and type directly.
- Drag the blue `move` strip to reposition the textbox.
- Drag the side or corner handles to resize it.
- Use `Fit text` to tighten the box around the text.
- Textbox records are maintained across PDF pages.
- Generate and download a searchable tagged PDF.

## Deployment

Upload all files and folders from this package to the root of the GitHub repository:

- `app.py`
- `iars_parser.py`
- `iars_pdf_editor.py`
- `requirements.txt`
- `packages.txt`
- `data/Master_Data.xlsx`

Replace the older files instead of mixing versions. After Streamlit finishes redeploying, press `Ctrl + F5` once.

## Master Data

The included `data/Master_Data.xlsx` is unchanged from the uploaded `Master_Data(2).xlsx`.

## Tested environment

The dependency versions remain pinned in `requirements.txt`, including Streamlit 1.58.0 for Streamlit Cloud deployment.
