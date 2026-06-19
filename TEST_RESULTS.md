# IARS v2.6 Test Results

Test date: June 19, 2026

## Focused explanation-rule tests

Passed for all required phrases:

1. `The overage occurred because ...`
2. `The shortage occurred because ...`
3. `The discrepancy occurred because ...`
4. `This occurred due to ...`
5. `This occured due to ...`

The words after each phrase were returned as the Explanation.

## INCOMPLETE DETAILS IN PCV tests

Passed:

- Generic title + narrative containing PAYEE and AMOUNT -> `INCOMPLETE DETAILS IN PCV - PAYEE, AMOUNT`
- Existing PAYEE title + narrative containing PAYEE and AMOUNT -> adds AMOUNT only
- Existing PAYEE and AMOUNT title + same narrative -> no duplicate fields

## 2026IAD222 integration test

The tagged Vet City Marikina report was processed five consecutive times with identical output.

Confirmed results:

- Issue 1 title: `CASH OVERAGE - P10,996.31`
- Issue 1 Explanation begins: `Some revolving fund transactions were initially paid using the custodian's personal funds ...`
- Issue 2 title: `INCOMPLETE DETAILS IN PCV - PAYEE, AMOUNT`
- Issue 6 Explanation: `Usage of P3,337.00 cash sales to fund the operation's expenses since their revolving fund was insufficient.`
- Seven findings retained

## Cross-page continuation test

Passed:

- Page 2 opening continuation was appended to Issue 1.
- Page 3 opening continuation was appended to Issue 6.
- Exhibit pages were excluded from continuation handling.

## Regression tests

Successful nonempty extraction was confirmed for 11 PDFs:

- 2026IAD013 - Angelica Cuevas: 5 rows
- 2026IAD209 - Michelle Mesa: 3 rows
- 2026IAD211 - Mia Montejo: 1 row
- 2026IAD212 - Mirz Dula-ugon: 1 row
- 2026IAD214 - Jennifer Cabintoy: 1 row
- 2026IAD215 - Jennel Kate Fortin: 6 rows
- 2026IAD220 - Jugine Corpuz: 4 rows
- 2026IAD221 - Timothy So: 1 row
- CamScanner 06-17-2026 23.10: 8 rows
- EMERITO: 8 rows
- 2026IAD222 - Vet City Marikina: 7 rows

## Technical verification

- `iars_parser.py` compilation: passed
- `app.py` compilation: passed
- `iars_pdf_editor.py` compilation: passed
- Five-run deterministic 2026IAD222 extraction: passed
- Required output columns preserved
- Existing Master Data preserved

## Limitation

The rules were validated against the listed files and focused test cases. Reports with materially different layouts or wording may still require a future parser adjustment.
