# IARS v2.3 Test Results

Date tested: June 19, 2026

## 1. Python and Streamlit checks

- `app.py` compiled successfully.
- `iars_parser.py` compiled successfully.
- `iars_pdf_editor.py` compiled successfully.
- Streamlit 1.58 `AppTest` completed with zero application exceptions.
- Both application tabs loaded:
  - Generate Extraction
  - PDF Tagging Editor
- A local Streamlit 1.58 server started successfully and passed its health endpoint.

## 2. Frontend editor browser tests

The exact v2.3 HTML, CSS, and JavaScript were mounted in headless Chromium with a browser test harness.

Passed:

- double-right-click creates one textbox
- click inside the box accepts typing
- text is written to the browser-local backup during typing
- clicking outside synchronizes text to the component state
- page 1 text remains after switching to page 2 and returning to page 1
- page 2 text remains stored at the same time as page 1 text
- `Fit text` reduced a test textbox from approximately 24 px high to 18 px high
- text CSS remained `white-space: nowrap`
- one all-page state contained both page 1 and page 2 textbox records
- JavaScript syntax check passed with Node.js 22

Tested text values:

- Page 1: `Task ID: 001`
- Page 2: `Auditor: Sarina Amuraw`

## 3. Tagged PDF generation

A four-page scanned audit report was tagged on pages 1 and 2.

Passed:

- generated PDF opened successfully
- page count remained four
- `Task ID: 001` was machine-readable
- `Auditor: Sarina Amuraw` was machine-readable
- tag borders rendered correctly
- text was vertically centered with close padding
- labels stayed on one line
- all pages rendered successfully at 160 DPI

## 4. Parser regression tests

The unchanged parser and current Master Data were tested against:

- 2026IAD013 - Angelica Cuevas: 5 extracted rows
- 2026IAD209 - Michelle Mesa: 3 extracted rows
- 2026IAD215 - Jennel Kate Fortin: 6 extracted rows
- CamScanner 06-17-2026 23.10: 8 extracted rows

All four reports produced nonempty outputs.

## 5. Master Data verification

`data/Master_Data.xlsx` is byte-for-byte identical to the uploaded `Master_Data(2).xlsx`.

SHA-256:

`b934f7f417ffcbffba6c63adad647b9e38053e6bec9d750d447216bf6666488a`

## Deployment note

After replacing the GitHub files, allow Streamlit Cloud to redeploy and use Ctrl+F5 once so the browser loads the v2.3 component name and current JavaScript.
