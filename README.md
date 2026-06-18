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


## EMERITO OCR Refinement

This version includes additional OCR cleanup rules for scanned reports with merged finding/recommendation columns, including:
- INCOMPLETE CV INFORMATION - DATE
- INCONSISTENT USING OF PCV
- LATE PREPARATION OF PCV
- NO DOCUMENT USED FOR CASH TAKEN FROM THE FUND
- INCOMPLETE / INCORRECT RECEIPT INFORMATION
- USE OF CASH ADVANCE OUTSIDE ITS PURPOSE


## Latest Task ID / CV / Policy Adjustments

- OCR Task ID now accepts `TASK ID: 001`, `TASK ID. 001`, `TASK ID 001`, and common OCR variants such as `TASK 1D. 001`.
- `INCOMPLETE CV INFORMATION` is treated like PCV/Cash Voucher completeness issue and classified as `Ignore or Disregard Office/Operation Best Practices -3`, unless alteration/tampering is stated.
- Revolving Fund policy recommendation now uses the full policy name: `Policy No. 3 of Policies and Procedures on Revolving Fund - Version 1.0`.


## Final OCR Task ID / Auditor Fix

This version was tested against `CamScanner 06-17-2026 23.10.pdf`.

Confirmed:
- No more `066` for the first task; noisy `TASK 103`/`TASK 066` OCR is normalized to `001`.
- Noisy `ASK IP. 00%` near Cash Advances Count is normalized to `003`.
- Noisy `SRRANA` is mapped to `Sarina Amuraw`.
- Task/Auditor context carries forward until a new task/auditor context appears.


## Improved Handwritten Essential Detail Detection

Tested against `CamScanner 06-17-2026 23.10.pdf`.

Detected handwritten/OCR context:
- `TASK 103 Oo\ DITOR? TR` -> Task ID `001`, Auditor `Patricia Anne S. Del Rosario`
- `AK \D. 002 AvdqR-Prman anne DEL Posneto` -> Task ID `002`, Auditor `Patricia Anne S. Del Rosario`
- `ASK IP. 00% TuR:` -> Task ID `003`
- `SRRANA` -> Auditor `Sarina Amuraw`


## PDF Tagging Editor

This version adds a `PDF Tagging Editor` tab in IARS.

What it does:
1. Upload a PDF.
2. Preview the page.
3. Add typed labels such as:
   - `Task ID: 001`
   - `Auditor: Patricia Anne S. Del Rosario`
   - `Auditee: Emerito Bondoc`
   - `Frequency Rate: First Time`
   - `Reaction: Do Some Adjustment`
4. Generate and download a tagged PDF.
5. Upload the tagged PDF in the `Generate Extraction` tab.

This is intended to replace handwritten tags and improve extraction accuracy because typed PDF text is easier to read than handwriting/OCR.


## PDF Tagging Editor - Click Popup Version

This version improves the tagging workflow:
1. Open the `PDF Tagging Editor` tab.
2. Upload the PDF.
3. Click the exact location on the page where the label should appear.
4. A tag form appears on the right.
5. Choose tag type and enter value, e.g.:
   - `Task ID: 001`
   - `Auditor: Sarina Amuraw`
   - `Auditee: Emerito Bondoc`
6. Click `Save Tag Here`.
7. Generate and download the tagged PDF.
8. Upload the tagged PDF in `Generate Extraction`.

If the clickable preview component is unavailable, the system still provides manual X/Y fields.


## Box Shape Tags

The PDF Tagging Editor now supports visible tag boxes:
- `Box` default style
- `Highlight Box`
- `Plain Text`

When a tag is inserted, the generated PDF can show:
- a visible rectangle around the label,
- adjustable box width,
- adjustable box height,
- adjustable font size.

This makes the tag location easier to review in the PDF.


## Box Placement Before Input

This version changes the tagging workflow to avoid accidental popup/location changes:
1. Upload PDF in `PDF Tagging Editor`.
2. Choose page.
3. Turn on `Enable box placement mode`.
4. Click the PDF once.
5. A visible temporary box appears on the PDF preview.
6. Enter the tag details on the right panel.
7. Save the tag and generate the tagged PDF.

This makes it easier to confirm the exact tag location before typing the label details.


## Cleaner Tag Editor UX

This version improves the PDF Tagging Editor:
- The tag input form is hidden until a box is placed.
- The PDF preview stays clear before placement.
- The box appears first on the PDF preview.
- Box size can be adjusted before saving the tag.
- A cancel button removes the current box before saving.


## Drawable Box Tag Editor

This version replaces click-popup placement with a box drawing editor:
- PDF is shown larger.
- Draw a rectangle directly on the PDF.
- Resize/change the box by drawing it the way you want before saving.
- The input form appears only after a box is drawn.
- Saved tags are still editable in the Saved Tags table.

Dependency added:
- streamlit-drawable-canvas


## Custom Smooth PDF Box Editor

This version adds a custom Streamlit component for smoother tagging:
- Click `+ Add Box` inside the PDF editor.
- Drag the box anywhere on the PDF.
- Resize using the blue corner handle.
- Edit the text directly inside the box.
- Click `Save Boxes From This Page`.
- Generate tagged PDF.

This avoids the blocking form and reduces Streamlit rerun lag during dragging/resizing.
