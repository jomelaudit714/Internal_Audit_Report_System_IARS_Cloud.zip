# Internal Audit Report System (IARS) v2.2

This build uses the v2.1 Streamlit Components v2 PDF textbox editor as its starting ground and fixes the textbox focus/click issue.

## PDF editor workflow

1. Upload a PDF in **PDF Tagging Editor**.
2. Right-click twice at nearly the same PDF location to create a textbox.
3. Click inside the textbox and type directly.
4. Drag the top strip to reposition the textbox.
5. Drag any blue edge or corner handle to resize it.
6. Generate and download the tagged PDF.
7. Upload the tagged PDF under **Generate Extraction**.

## Important v2.2 fix

The previous component rebuilt the textbox DOM during `pointerdown`/`focus`. That removed the active contenteditable element before the browser could place the caret, so the textbox appeared but did not accept typing. v2.2 updates only the selection styling when the textbox is clicked, preserving the live contenteditable element and caret.

## Main files

- `app.py` - Streamlit application
- `iars_parser.py` - existing extraction and classification logic
- `iars_pdf_editor.py` - Components v2 PDF textbox editor
- `data/Master_Data.xlsx` - current Master Data supplied by the user
- `requirements.txt` - Python dependencies
- `packages.txt` - system dependency for OCR
- `TEST_RESULTS.md` - verification performed for this build
