# Internal Audit Report System (IARS) v2.3

This version starts from IARS v2.2 and corrects two PDF editor issues:

1. Textboxes and their text now remain saved when moving to another PDF page and returning.
2. The textbox is tighter around the text, and resizing no longer pushes the label into another line.

## PDF editor workflow

1. Upload a PDF under **PDF Tagging Editor**.
2. Right-click twice at nearly the same location to create a textbox.
3. Click inside the box and type the tag.
4. Drag the blue **move** tab to reposition the textbox.
5. Drag any blue side or corner handle to resize it.
6. Click **Fit text** to tighten the selected box around the label.
7. Change PDF pages as needed. Existing boxes remain available when returning to a page.
8. Generate and download the tagged PDF.
9. Upload the tagged PDF under **Generate Extraction**.

## v2.3 persistence design

- One Components v2 state stores textbox data for every PDF page.
- The component key stays the same when the page number changes.
- A browser-local backup is updated while typing.
- Clicking outside the box, pressing Enter, changing pages, dragging, or resizing synchronizes the editor state to Streamlit.

## v2.3 box and text improvements

- Text padding reduced to 1 px vertically and 3 px horizontally.
- Text remains on one line instead of wrapping downward.
- Font size automatically decreases when a box is made narrower or shorter.
- The default textbox is smaller and closer to the text.
- **Fit text** automatically adjusts the box to the selected label.
- Generated PDF tags use tight padding, vertical centering, and automatic font fitting.

## Main files

- `app.py` - Streamlit application and tagged-PDF generation
- `iars_parser.py` - existing extraction and classification rules
- `iars_pdf_editor.py` - Components v2 PDF textbox editor
- `data/Master_Data.xlsx` - current Master Data supplied by the user
- `requirements.txt` - Python dependencies
- `packages.txt` - OCR system dependency
- `TEST_RESULTS.md` - verification record for this release
