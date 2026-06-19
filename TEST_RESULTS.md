# IARS v2.2 Test Results

Test date: June 19, 2026

## Defect corrected

The v2.1 textbox was recreated during its own pointer-down/focus event. That destroyed the active contenteditable element before the browser could place the caret, causing the visible textbox to ignore typing.

The v2.2 editor changes selection styling without rebuilding the textbox DOM. It also explicitly focuses the contenteditable textbox after a click.

## Verification completed

### 1. Browser interaction test - passed 3/3

Automated in Chromium using the same HTML, CSS, and JavaScript included in `iars_pdf_editor.py`.

Each run verified:

- double-right-click created one textbox;
- clicking inside placed focus in the editable area;
- keyboard input was accepted;
- typed text remained in the textbox;
- typed text was written to component state;
- drag reposition changed X/Y coordinates;
- southeast-handle resize changed width/height;
- no JavaScript page errors occurred.

Test values: `Task ID: 001`, `Task ID: 002`, and `Task ID: 003`.

### 2. Static code tests - passed

- `app.py` Python compilation
- `iars_parser.py` Python compilation
- `iars_pdf_editor.py` Python compilation
- embedded editor JavaScript syntax validation through Node.js

### 3. Parser regression - passed 4/4

The existing parser produced records without exceptions for:

- `2026IAD209_Michelle_Mesa(2).pdf`
- `2026IAD220_Jugine_Corpuz.pdf`
- `2026IAD221_Timothy_So(1).pdf`
- `2026IAD013_ Angelica Cuevas.pdf`

### 4. Tagged-PDF output test - passed

- Inserted `Task ID: 901` into a sample audit PDF.
- Confirmed the text remained machine-readable through PyMuPDF extraction.
- Rendered all five output pages successfully at 120 DPI.
- Visually checked page 1: the textbox border and text were visible and correctly placed.

### 5. Master Data integrity - passed

The supplied `Master_Data(2).xlsx` was copied unchanged to `data/Master_Data.xlsx`.

- Source SHA-256: `b934f7f417ffcbffba6c63adad647b9e38053e6bec9d750d447216bf6666488a`
- Packaged SHA-256: `b934f7f417ffcbffba6c63adad647b9e38053e6bec9d750d447216bf6666488a`
- Match: `YES`

## Deployment note

The editor component name was changed to `iars_pdf_textbox_editor_v22` so Streamlit and the browser do not reuse the cached v2.1 frontend code.
