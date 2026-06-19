# IARS v2.4 Test Results

Test date: June 19, 2026

## Error reproduced and corrected

The Version 2.3 failure was reproduced during an actual Streamlit AppTest rerun after uploading a PDF:

`ValueError: Component 'iars_pdf_textbox_editor_v23' is not registered`

Root cause: the Components v2 editor was registered only during the first module import. Streamlit rebuilt its component registry on the next script rerun, but Python did not re-import the cached module.

Correction: Version 2.4 registers `iars_pdf_textbox_editor_v24` during every script run immediately before mounting it.

## Streamlit rerun tests

Passed without application exceptions:

1. Initial app load.
2. Upload a five-page PDF.
3. Mount the editor on Page 1.
4. Change to Page 2 and rerun.
5. Return to Page 1 and rerun.
6. Perform an additional unchanged rerun.

This directly tests the deployment path that failed in Version 2.3.

## Chromium editor interaction tests

An actual headless Chromium browser was used with the editor frontend in an isolated harness.

Passed:

- double-right-click creates one textbox
- click and type `Task ID: 001`
- text commits to the editor state
- Page 1 -> Page 2 -> Page 1 retains the encoded text
- internal text padding is `1px 3px`
- text uses `white-space: nowrap`
- `Fit text` produced an approximately 18-pixel-high textbox
- drag reposition works
- southeast-handle resize works
- no JavaScript page errors

## PDF output tests

A two-page PDF was generated and tagged with different text on each page.

Passed:

- Page 1 contains searchable `Task ID: 001`
- Page 2 contains searchable `Auditor: Sarina Amuraw`
- both pages rendered successfully to PNG
- no clipped or overlapping tag text was observed

## Parser regression tests

Nonempty extraction results were generated for:

- 2026IAD013 - Angelica Cuevas: 5 rows
- 2026IAD209 - Michelle Mesa: 3 rows
- 2026IAD215 - Jennel Kate Fortin: 6 rows
- CamScanner 06-17-2026 23.10: 8 rows

## Master Data verification

SHA-256 of uploaded `Master_Data(2).xlsx`:

`b934f7f417ffcbffba6c63adad647b9e38053e6bec9d750d447216bf6666488a`

The included `data/Master_Data.xlsx` has the same SHA-256 hash.

## Limitation

These tests cover the exact reproduced rerun error, repeated Streamlit mounting, frontend interaction logic, generated PDF output, and parser regressions. Final acceptance still requires one live check after GitHub and Streamlit Cloud redeployment because browser policies, deployment caching, or future platform changes are outside the ZIP itself.
