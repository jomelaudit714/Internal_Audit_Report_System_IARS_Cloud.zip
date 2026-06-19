# IARS v2.1 Test Results

Date tested: June 19, 2026

## 1. Python and Streamlit application checks

- `app.py` compiled successfully.
- `iars_parser.py` compiled successfully.
- `iars_pdf_editor.py` compiled successfully.
- Streamlit `AppTest` completed with zero application exceptions.
- Verified tabs:
  - Generate Extraction
  - PDF Tagging Editor
- Local Streamlit 1.58 server started successfully and passed the health endpoint check.

## 2. PDF editor JavaScript interaction tests

The editor JavaScript was syntax-checked with Node.js and tested in a simulated browser DOM.

Passed interactions:

- double-right-click creates exactly one textbox
- click inside and enter `Task ID: 001`
- text state persists after blur
- drag reposition changes X and Y coordinates
- corner resize changes width and height
- delete selected textbox
- load an existing saved textbox
- duplicate selected textbox
- clear all textboxes on the current page

The interaction test produced five state updates for create, text, drag, resize, and delete without continuous updates during pointer movement.

## 3. Tagged PDF generation and text readability

A searchable PDF was tagged with:

- `Task ID: 901`
- `Auditor: Sarina Amuraw`
- `Auditee: Michelle Mae Lazaro Mesa`

PyMuPDF successfully read all three inserted labels from the generated PDF.

## 4. Tagged PDF to parser round-trip

The tagged Michelle Mesa PDF was processed through the current `iars_parser.py`.

Confirmed:

- every extracted issue used Task ID `901`
- every extracted issue used `Sarina Amuraw` as Audited By1
- User was mapped from the Auditors sheet
- all three original findings remained present

## 5. Parser regression tests

The current parser and current Master Data were tested against:

- 2026IAD013 — Angelica Cuevas
- 2026IAD209 — Michelle Mesa
- 2026IAD215 — Jennel Kate Fortin
- CamScanner 06-17-2026 23.10 — multiple auditee/auditor/task report

All four reports generated nonempty extraction outputs. The existing issue titles, findings classifications, employee matching, and OCR Task ID behavior remained operational.

## 6. Master Data verification

The uploaded `Master_Data(2).xlsx` was successfully opened and all 15 expected worksheets were detected. The workbook was copied unchanged to `data/Master_Data.xlsx`.

## Test limitation

Automated tests cover application startup, editor logic, PDF generation, parser round-trip, and regression samples. Browser behavior can still vary slightly by device, browser zoom, or deployment environment, so final acceptance should include one live test in your Streamlit Cloud app after deployment.
