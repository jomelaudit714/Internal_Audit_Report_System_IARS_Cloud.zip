# Internal Audit Report System (IARS) v2.1

## Included files

- `app.py` — Streamlit interface, extraction workflow, and tagged-PDF generation
- `iars_parser.py` — current audit report extraction and classification logic
- `iars_pdf_editor.py` — smooth Streamlit Components v2 PDF textbox editor
- `requirements.txt` — Python dependencies for Streamlit Cloud
- `packages.txt` — installs Tesseract OCR
- `data/Master_Data.xlsx` — current Master Data supplied for this version
- `TEST_RESULTS.md` — verification performed before packaging

## PDF editor workflow

1. Open **PDF Tagging Editor**.
2. Upload the PDF only when tags are needed.
3. Select the page.
4. Double-right-click the same location on the PDF.
5. A textbox appears at that exact location.
6. Click inside the box and type, for example:
   - `Task ID: 001`
   - `Auditor: Sarina Amuraw`
   - `Auditee: Emerito Bondoc`
7. Press **Enter** or click outside the textbox to apply the text.
8. Drag the small top strip to reposition the box.
9. Drag any blue side or corner handle to resize the box.
10. Click **Generate Tagged PDF**, then download the result.
11. Upload the tagged PDF in **Generate Extraction**.

The box movement and resizing run in the browser and only update Streamlit after the interaction ends. This prevents the repeated reruns and lag experienced with `streamlit-drawable-canvas`.

## Important deployment notes

- Use Python 3.12 on Streamlit Community Cloud.
- Upload all files and the `data` folder while preserving the structure shown above.
- This version does **not** use:
  - `streamlit-drawable-canvas`
  - `streamlit-image-coordinates`
  - the old `pdf_box_editor` folder
- Replace your previous files with this package and delete the old `pdf_box_editor` folder if it is still in GitHub.

## Master Data

The included workbook contains the following sheets:

- Employees
- Classification_Matrix
- Response_Master
- Frequency_Master
- Auditors
- Audit_Types
- Issue_Title_Master
- Company_Overrides
- System_Objectives
- Data_Dictionary
- Response_Keywords
- Frequency_Keywords
- Prompt_Rules
- Manual_Override_Reasons
- Version_Control

## Current extraction rules preserved

The uploaded `iars_parser.py` was retained as the starting ground, including:

- OCR fallback for scanned PDFs
- multiple auditee handling
- multiple auditor handling
- Task ID carry-forward
- handwritten/OCR alias handling
- concise explanation, recommendation, and correction extraction
- cash overage/shortage and immateriality rules
- current issue-title and finding-category rules
