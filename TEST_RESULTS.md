# IARS v2.8 Test Results

Test date: June 19, 2026

## Target report verification

Report tested:

`tagged_2026IAD222_Vet_City_Marikina (2).pdf`

The report header contains:

`AUDITEE NAME: Dianne Susie Berbano and Jinky Venise Angel`

Issue 6 contains the tag:

`Auditee: Jinky`

Version 2.8 correctly performed the following sequence:

1. Resolved `Jinky` to the header name `Jinky Venise Angel`.
2. Applied the normal Master Data matching rule.
3. Returned `Jinky Venise Vicente Angel`.
4. Returned Employee ID `20250035`.
5. Applied the resolved auditee to Task ID `002` findings until changed.

Verified output:

- Issues 1-4: `Dianne Susie Capisonda Berbano` / `20180006` / Task ID `001`
- Issues 5-7: `Jinky Venise Vicente Angel` / `20250035` / Task ID `002`

## Repeatability test

The target report was processed five consecutive times.

Result: all five outputs were identical.

## Header-resolution unit tests

Passed:

- `Jinky` -> `Jinky Venise Angel`
- `Dianne` -> `Dianne Susie Berbano`
- `Jinky Venise` -> `Jinky Venise Angel`
- Unknown first name -> original tag retained
- Duplicate first name in header -> original tag retained to prevent guessing

## Regression tests

Nonempty extraction results were confirmed for ten existing reports:

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

## Code validation

Passed:

- `app.py` Python compilation
- `iars_parser.py` Python compilation
- `iars_pdf_editor.py` Python compilation

## PDF visual verification

The target PDF was rendered successfully into 11 page images. Page 2 visually confirms the issue-level tag `Auditee: Jinky` beside Task ID `002`.

## Master Data verification

SHA-256 of included `data/Master_Data.xlsx`:

`b934f7f417ffcbffba6c63adad647b9e38053e6bec9d750d447216bf6666488a`
