# IARS v2.5 Test Results

Test date: June 19, 2026

## Report 2026IAD222 reproduction test

The uploaded tagged PDF was processed with the Version 2.4 parser before the correction. The first row incorrectly returned:

- Issue Detail Issue: `REVOLVING FUND`
- Finding Category: `Ignore or Disregard Office/Operation Best Practices -3`

After the Version 2.5 correction, the same PDF returns:

- Issue Detail Issue: `CASH OVERAGE – P10,996.31`
- Finding Category: `Cash/Fund/Collection Overage (₱1,000.00 and above) -4`

The parser also retained the expected Task ID `001`, auditor `Patricia Anne S. Del Rosario`, auditee match, and `2nd Time` frequency.

## Repeated deterministic test

The complete 2026IAD222 extraction was run five consecutive times.

Passed:

- identical output hash on all five runs
- identical seven extracted rows on all five runs
- first issue remained `CASH OVERAGE – P10,996.31`
- no audit activity heading appeared in Issue Detail Issue

## Synthetic title-selection tests

Passed:

- `REVOLVING FUND` followed by `CASH OVERAGE – P10,996.31` -> captures `CASH OVERAGE – P10,996.31`
- `PETTY CASH FUND` followed by `NO CASH SHORTAGE/OVERAGE` -> captures `NO CASH SHORTAGE/OVERAGE`
- `SALES AND COLLECTION` with merged tags followed by `CASH SHORTAGE: (P3,274.00)` -> captures the cash shortage
- `REVOLVING FUND COUNT` followed by `INCOMPLETE DETAILS IN PCV` -> captures the PCV issue
- `MIXING OF PETTY CASH AND REVOLVING FUND` remains a valid true issue and is not discarded

## Searchable PDF regression tests

Nonempty extraction results and valid issue titles were confirmed for:

- 2026IAD209 - Michelle Mesa: 3 rows
- 2026IAD211 - Mia Montejo: 1 row
- 2026IAD212 - Mirz Dula-ugon: 1 row
- 2026IAD214 - Jennifer Cabintoy: 1 row
- 2026IAD215 - Jennel Kate Fortin: 6 rows
- 2026IAD220 - Jugine Corpuz: 4 rows
- 2026IAD221 - Timothy So: 1 row
- 2026IAD013 - Angelica Cuevas: 5 rows

No extracted Issue Detail Issue matched an activity heading.

## OCR/scanned PDF regression tests

Passed:

- EMERITO.pdf: 8 rows
- CamScanner 06-17-2026 23.10.pdf: 8 rows

The existing handwritten Task ID, auditor, auditee, frequency, and reaction carry-forward logic remained operational.

## Code verification

Passed:

- `app.py` Python compilation
- `iars_parser.py` Python compilation
- `iars_pdf_editor.py` Python compilation
- exact uploaded Master Data SHA-256 match

## Master Data verification

SHA-256 of the included `data/Master_Data.xlsx`:

`b934f7f417ffcbffba6c63adad647b9e38053e6bec9d750d447216bf6666488a`

This matches the uploaded `Master_Data(2).xlsx` exactly.

## Deployment note

The parser and source code were tested locally against the uploaded report and the regression files. The live Streamlit Cloud environment should still be checked once after GitHub redeployment because platform caching and browser behavior are external to the ZIP.
