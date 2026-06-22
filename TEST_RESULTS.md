# IARS v2.9 Test Results

## Requested output rules

- `#` column: blank for every generated finding row.
- `Encoded Date`: today's system date in `YYYY-MM-DD` format.
- `Date Reported`: report date converted to `YYYY-MM-DD` format.

## Target report verification

Test report: `tagged_2026IAD222_Vet_City_Marikina (2).pdf`

- Findings generated: 7
- `#`: blank in all 7 rows
- `Encoded Date`: `2026-06-22` in all 7 rows during testing
- `Date Reported`: `2026-06-09` in all 7 rows
- Target report was processed five consecutive times with identical output.

## Date-format tests

Passed input conversion tests for:

- `June 9, 2026`
- `JUNE 9, 2026`
- `Jun 9 2026`
- `06/09/2026`
- `2026-06-09`
- `June 9th, 2026`

All converted to `2026-06-09`.

## Regression tests

Nine audit reports passed extraction regression testing:

- 2026IAD209 Michelle Mesa
- 2026IAD211 Mia Montejo
- 2026IAD212 Mirz Dula-ugon
- 2026IAD214 Jennifer Cabintoy
- 2026IAD215 Jennel Kate Fortin
- 2026IAD220 Jugine Corpuz
- 2026IAD221 Timothy So
- 2026IAD013 Angelica Cuevas
- 2026IAD222 Vet City Marikina

Confirmed for every generated row:

- blank `#` value
- ISO `Encoded Date`
- ISO `Date Reported`, or `None` only when the source report does not contain a recognizable report date

## Technical checks

- `app.py`: Python compilation passed
- `iars_parser.py`: Python compilation passed
- `iars_pdf_editor.py`: Python compilation passed
- Generated Excel workbook opened successfully
- Key output range verified
- Formula-error scan returned zero errors
