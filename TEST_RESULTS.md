# IARS v2.7 Test Results

## Target report

`tagged_2026IAD222_Vet_City_Marikina (2).pdf`

## Required outcome

| Issue | Frequency | Reaction |
|---|---|---|
| CASH OVERAGE - P10,996.31 | Second Time | Performed SAME offense |
| INCOMPLETE DETAILS IN PCV - PAYEE, AMOUNT | First Time | Do Some Adjustment |
| AMOUNT DISCREPANCY IN PCV AS AGAINST RECEIPT | First Time | Do Some Adjustment |
| NO ATTACHED SUPPORTING DOCUMENTS | First Time | Do Some Adjustment |
| INCOMPLETE RECEIPT INFORMATION | Second Time | Performed SAME offense |
| CASH SHORTAGE: (P3,274.00) | First Time | Do Some Adjustment |
| NON-COMPLIANCE WITH REMITTANCE SCHEDULE | First Time | Do Some Adjustment |

## Tests performed

1. Target report processed five consecutive times with identical results: PASS.
2. Frequency on Issue 1 did not carry to Issues 2-4: PASS.
3. Frequency on Issue 5 did not carry to Issues 6-7: PASS.
4. `2nd Time` normalization to `Second Time`: PASS.
5. `second time` normalization to `Second Time`: PASS.
6. First through Seventh Time normalization checks: PASS.
7. Second Time Reaction evaluated as `Performed SAME offense`: PASS.
8. Previous-audit narrative without carry-forward still evaluated as Second Time: PASS.
9. Auditee, Auditor and Task ID carry-forward remained active: PASS.
10. Python compilation for app.py, iars_parser.py and iars_pdf_editor.py: PASS.
11. Regression extraction completed without errors on 11 reports: PASS.

## Regression reports

- 2026IAD013_ Angelica Cuevas.pdf - 5 rows
- 2026IAD209_Michelle_Mesa(2).pdf - 3 rows
- 2026IAD211_Mia_Montejo.pdf - 1 row
- 2026IAD212_Mirz_Dula-ugon.pdf - 1 row
- 2026IAD214_Jennifer_Cabintoy.pdf - 1 row
- 2026IAD215_Jennel Kate Fortin(1).pdf - 6 rows
- 2026IAD220_Jugine_Corpuz(2).pdf - 4 rows
- 2026IAD221_Timothy_So(1).pdf - 1 row
- CamScanner 06-17-2026 23.10.pdf - 8 rows
- EMERITO.pdf - 8 rows
- tagged_2026IAD222_Vet_City_Marikina (2).pdf - 7 rows

## Master Data verification

The SHA-256 hash of the packaged `data/Master_Data.xlsx` matches the uploaded `Master_Data(2).xlsx`:

`b934f7f417ffcbffba6c63adad647b9e38053e6bec9d750d447216bf6666488a`
