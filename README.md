# Internal Audit Report System (IARS) v2.7

## Main correction

Version 2.7 fixes Frequency and Reaction evaluation.

### Frequency is issue-specific

`Frequency Rate:` and `Frequency:` tags apply only to the issue where the tag is placed. They do not carry forward to the following issue.

The following tags still carry forward until replaced:

- Auditee
- Auditor
- Task ID

### Frequency normalization

The parser normalizes ordinal tags to the IARS dropdown values:

- `1st Time` / `First Time` -> `First Time`
- `2nd Time` / `Second Time` -> `Second Time`
- `3rd Time` / `Third Time` -> `Third Time`
- through `Seventh Time`

### Reaction for repeated findings

When Frequency is `Second Time` or higher, Reaction is evaluated as:

`Performed SAME offense`

It is no longer evaluated as `Do Some Adjustment`.

### Existing previous-audit rule

When no explicit frequency tag is present but the issue states that the same finding was noted in a previous audit, the issue is evaluated as:

- Frequency: `Second Time`
- Reaction: `Performed SAME offense`

## Verified 2026IAD222 result

- Issue 1 - `CASH OVERAGE - P10,996.31`: Second Time / Performed SAME offense
- Issues 2 to 4: First Time / Do Some Adjustment
- Issue 5 - `INCOMPLETE RECEIPT INFORMATION`: Second Time / Performed SAME offense
- Issues 6 and 7: First Time / Do Some Adjustment

## Preserved corrections

- True issue title is captured instead of activity headings such as Revolving Fund.
- Explanation captures cause statements after overage/shortage/discrepancy phrases.
- Incomplete PCV details are combined without duplication, e.g. `PAYEE, AMOUNT`.
- The PDF textbox editor remains unchanged.

## Deployment

Upload and replace all files in the repository root:

- `app.py`
- `iars_parser.py`
- `iars_pdf_editor.py`
- `requirements.txt`
- `packages.txt`
- `data/Master_Data.xlsx`

Do not mix files from older ZIP versions. After Streamlit redeploys, press `Ctrl + F5` once.

## Master Data

The included `data/Master_Data.xlsx` is unchanged from the uploaded `Master_Data(2).xlsx`.
