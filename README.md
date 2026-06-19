# Internal Audit Report System (IARS) v2.6

## Main parser corrections

### 1. Cause statements now populate Explanation

When an issue narrative contains any of the following phrases, IARS captures the words immediately after the phrase as the Explanation:

- `The overage occurred because ...`
- `The shortage occurred because ...`
- `The discrepancy occurred because ...`
- `The overage/shortage/discrepancy occurred due to ...`
- `This occurred due to ...`
- `This occured due to ...` (common misspelling also supported)

The cause statement is prioritized before the existing auditee-explanation patterns.

### 2. INCOMPLETE DETAILS IN PCV combines missing fields without duplicates

The parser now applies this rule:

- If the title is only `INCOMPLETE DETAILS IN PCV`, collect all specific incomplete fields stated in the narrative.
- If the title already includes one or more fields, preserve those fields and add only other fields stated in the narrative.
- Do not repeat fields already present in the title.

Example:

- Existing title: `INCOMPLETE DETAILS IN PCV - PAYEE`
- Narrative: `... incomplete details, particularly in the payee and amount fields.`
- Final title: `INCOMPLETE DETAILS IN PCV - PAYEE, AMOUNT`

### 3. Cross-page finding continuation

A finding narrative that continues at the top of the next report page without repeating the issue number is appended to the preceding finding. Exhibit pages are excluded. This allows cause statements such as `This occurred due to ...` on the next page to be captured correctly.

## Preserved functionality

- PDF textbox editor from Version 2.5
- Double-right-click textbox creation
- Direct typing, drag repositioning, and drag resizing
- PDF page-state persistence
- True issue-title selection instead of activity headings
- Existing extraction, OCR, tagging, scoring, and classification rules
- Existing `data/Master_Data.xlsx`

## Deployment

Replace all repository files with the contents of this ZIP:

- `app.py`
- `iars_parser.py`
- `iars_pdf_editor.py`
- `requirements.txt`
- `packages.txt`
- `data/Master_Data.xlsx`

After Streamlit finishes redeploying, press `Ctrl + F5` once.
