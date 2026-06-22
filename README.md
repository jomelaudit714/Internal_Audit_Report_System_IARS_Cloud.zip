# Internal Audit Report System (IARS) v2.8

## Main correction: first-name auditee tags

Version 2.8 resolves an abbreviated auditee tag against the full names written in the report header before applying the normal Master Data matching rule.

Example:

- Report header: `AUDITEE NAME: Dianne Susie Berbano and Jinky Venise Angel`
- Issue tag: `Auditee: Jinky`
- Header name selected: `Jinky Venise Angel`
- Final Master Data result: `Jinky Venise Vicente Angel` with Employee ID `20250035`

## Matching order

1. Read the report's `AUDITEE NAME:` field.
2. Separate the listed auditees when the field contains `and`, `/`, or `&`.
3. Compare the typed auditee tag with those header names.
4. A first-name-only tag must match the first name of exactly one listed auditee.
5. Pass the selected full header name through the existing Master Data employee matching rule.
6. Carry the resolved auditee forward until a new auditee tag is encountered, following the existing auditee carry-forward rule.

## Ambiguity protection

The parser does not guess when two header names have the same first name. In that case, it retains the original tag so that a more specific auditee name can be supplied.

## Existing rules preserved

- Frequency and Reaction remain issue-specific and do not carry to later issues.
- Auditee, Auditor, and Task ID retain their existing carry-forward behavior.
- `Second Time` and higher continue to produce `Performed SAME offense`.
- The true issue-title, explanation-cause, and incomplete-PCV-detail rules remain active.
- The Components v2 PDF textbox editor remains unchanged.

## PDF textbox editor

- Double-right-click the same PDF location to add a textbox.
- Click inside the textbox and type directly.
- Drag the blue `move` strip to reposition the textbox.
- Drag the side or corner handles to resize it.
- Use `Fit text` to tighten the box around the text.
- Textbox records are maintained for all PDF pages.
- Generate and download a searchable tagged PDF.

## Deployment

Replace the existing repository files with all files from this package:

- `app.py`
- `iars_parser.py`
- `iars_pdf_editor.py`
- `requirements.txt`
- `packages.txt`
- `data/Master_Data.xlsx`

After Streamlit finishes redeploying, press `Ctrl + F5` once.

## Master Data

The included `data/Master_Data.xlsx` is unchanged from the current approved Master Data workbook.

## v2.9 - Blank Number Column and ISO Date Formatting

This version changes the generated extraction output as follows:

- The `#` column remains present but every generated data row is blank.
- `Encoded Date` uses the system date on the day the extraction is generated and is displayed as `YYYY-MM-DD`.
- `Date Reported` is converted from common report-date formats, such as `June 9, 2026`, to `YYYY-MM-DD`.
- Existing extraction, auditee matching, frequency, explanation, finding classification, and PDF editor rules are preserved.
