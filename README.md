# Internal Audit Report System V2 - Structured Table Parser

This is a clean replacement version designed to avoid the chaotic regex patches.

## Main change
This version uses `pdfplumber.page.extract_tables()` first, so issue details and recommendations are captured by table columns instead of mixed paragraph text.

## Run locally

```cmd
pip install -r requirements.txt
python -m streamlit run app.py
```

## Upload to Streamlit
Upload these files to GitHub:
- app.py
- iars_parser.py
- requirements.txt
- README.md

Main file path:
```text
app.py
```