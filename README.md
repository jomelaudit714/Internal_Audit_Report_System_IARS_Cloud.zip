# Internal Audit Report System (IARS) v2.4

## Main correction

Version 2.4 fixes the deployment error that appeared after uploading a PDF or changing pages:

`Component 'iars_pdf_textbox_editor_v23' is not registered`

Streamlit resets the Components v2 registry during every script rerun, while imported Python modules remain cached. The previous version registered the editor only when `iars_pdf_editor.py` was first imported. Version 2.4 registers the editor safely during every app rerun before mounting it.

## PDF textbox editor

- Double-right-click the same PDF location to add a textbox.
- Click inside the textbox and type directly.
- Drag the blue `move` strip to reposition the textbox.
- Drag the side or corner handles to resize it.
- Use `Fit text` to tighten the box around the text.
- Text stays on one line and uses tight internal padding.
- Textbox records are maintained for all PDF pages.
- Generate and download a searchable tagged PDF.

## Deployment

Upload all files and folders from this package to the root of the GitHub repository:

- `app.py`
- `iars_parser.py`
- `iars_pdf_editor.py`
- `requirements.txt`
- `packages.txt`
- `data/Master_Data.xlsx`

Replace the older files rather than mixing versions. After Streamlit redeploys, press `Ctrl + F5` once.

## Master Data

The included `data/Master_Data.xlsx` is an unchanged copy of the uploaded `Master_Data(2).xlsx`.

## Tested environment

The dependency versions in `requirements.txt` are pinned to the Streamlit Cloud environment used for testing, including Streamlit 1.58.0.
