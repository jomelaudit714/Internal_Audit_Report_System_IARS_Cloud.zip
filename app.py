
import os
import re
from io import BytesIO
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

try:
    import pdfplumber
except Exception:
    pdfplumber = None

try:
    from supabase import create_client
except Exception:
    create_client = None


st.set_page_config(
    page_title="Internal Audit Report System",
    page_icon="📄",
    layout="wide"
)

SYSTEM_NAME = "Internal Audit Report System"
SYSTEM_SHORT = "IARS"

HEADERS = [
    "#","Encoded Date","Type","Date Reported","Audit Reference","ID No","Name",
    "Task ID","Scope Date","Year","Findings","Issue Detail Issue","Explanation",
    "Recommendation1","Recommendation2","Audited By1","Audited By2","Reaction",
    "Frequency","Correction","Sanction","Case Status","Score","Improve Score",
    "Net Score","Audit Unit","User"
]

AUDITORS = [
    "Noel Buena", "Jomel Santiago", "Trece Generato Jr.", "Antonio P. Bides",
    "Jed Laserna", "Cris Canonoy", "Joshua Christopher Catis",
    "Sarina Amuraw", "Patricia Anne Del Rosario",
]

FINDINGS_DROPDOWN = [
    "Stock Overage (₱3,000.00 and above) -4",
    "Stock Overage (below ₱3,000.00) -2",
    "Stock Shortage (₱3,000.00 and above) -8",
    "Stock Shortage (below ₱3,000.00) -4",
    "Cash/Fund/Collection Overage (₱1,000.00 and above) -4",
    "Cash/Fund/Collection Overage (below ₱1,000.00) -2",
    "Cash/Fund/Collection Shortage (₱3,000.00 and above) -8",
    "Cash/Fund/Collection Shortage (below ₱3,000.00) -4",
    "Non-Remittance Of Collection (₱3,000.00 and above) -8",
    "Non-Remittance Of Collection (below ₱3,000.00) -4",
    "Delayed Deposits -3",
    "Late/Non-Issuance Of Receipts -6",
    "Omission & Alteration Of Details in Documents -7",
    "Unavailable or Unreliable Inventory Records -6",
    "Missing, Misused or Lost Of Documents/Asset(s) -3",
    "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4",
    "Ignore or Disregard Office/Operation Best Practices -3",
    "Manipulate To Deceive or Defraud for Personal Gain -10",
    "Unethical Act or Behavior -6",
    "Unobservant/Failure To Follow Instructed Procedures -2",
    "Unauthorized Use of Asset(s) -2",
    "Delivery and/or Computation, Reporting Error(s) -2",
    "Immaterial Findings 3",
    "No Findings 10",
]

REACTION_OPTIONS = [
    "", "Complied with previous recommendation", "Established guidelines",
    "Acknowledged the issue & will do correction", "Maintaining Status Quo",
    "Performed SAME offense", "Diverted the issue", "Low priority",
    "Undertake unfavorable approach", "Uncooperative", "Do Some Adjustment",
]

RESPONSE_RATE = {
    "Complied with previous recommendation": 4,
    "Established guidelines": 3,
    "Acknowledged the issue & will do correction": 2,
    "Maintaining Status Quo": 1,
    "Performed SAME offense": -3,
    "Diverted the issue": -3,
    "Low priority": -3,
    "Undertake unfavorable approach": -2,
    "Uncooperative": -4,
    "Do Some Adjustment": 0,
    "": 0,
    "None": 0,
}

FREQUENCY_OPTIONS = [
    "", "Not Applicable", "First Time", "Second Time", "Third Time",
    "Fourth Time", "Fifth Time", "Sixth Time", "Seventh Time",
]

FREQUENCY_RATE = {
    "Not Applicable": 1,
    "First Time": 1,
    "Second Time": 2,
    "Third Time": 3,
    "Fourth Time": 4,
    "Fifth Time": 5,
    "Sixth Time": 6,
    "Seventh Time": 7,
    "": 1,
    "None": 1,
}


def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def get_supabase():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    if not url or not key or create_client is None:
        return None
    return create_client(url, key)


def cloud_enabled():
    return get_supabase() is not None


def extract_pdf_text(uploaded_file):
    if pdfplumber is None:
        st.error("pdfplumber is not installed.")
        return ""
    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            text += "\n" + (page.extract_text() or "")
    return text


def find_after_label(text, labels):
    if isinstance(labels, str):
        labels = [labels]
    for label in labels:
        pattern = rf"{re.escape(label)}\s*[:\-]\s*([^\n\r]+)"
        match = re.search(pattern, text or "", re.IGNORECASE)
        if match:
            return clean_text(match.group(1))
    return "None"


def extract_header(text):
    date_reported = find_after_label(text, ["DATE"])
    audit_reference = find_after_label(text, ["REF"])
    auditee_name = find_after_label(text, ["AUDITEE NAME"])
    period = find_after_label(text, ["PERIOD DATE", "COVERING PERIOD", "SCOPE DATE"])
    task_id = find_after_label(text, ["TASK ID"])

    scope_date = "None"
    year = "None"
    dates = re.findall(r"([A-Za-z]+)\s+(\d{1,2}),\s*(\d{4})", period)
    if len(dates) >= 2:
        start, end = dates[0], dates[-1]
        scope_date = f"{start[0]} {start[1]} to {end[0]} {end[1]},"
        year = end[2]
    elif len(dates) == 1:
        m = dates[0]
        scope_date = f"{m[0]} {m[1]},"
        year = m[2]

    if year == "None":
        ym = re.search(r"\b(20\d{2})\b", date_reported)
        if ym:
            year = ym.group(1)

    return {
        "date_reported": date_reported,
        "audit_reference": audit_reference,
        "auditee_name": auditee_name,
        "period": period,
        "scope_date": scope_date,
        "year": year,
        "task_id": task_id,
    }


def extract_money_amounts(value):
    amounts = []
    for m in re.finditer(r"(?:₱|P)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2}))", value or "", re.I):
        try:
            amounts.append(float(m.group(1).replace(",", "")))
        except Exception:
            pass
    return amounts


def parse_score(findings_value):
    m = re.search(r"(-?\d+)\s*$", findings_value or "")
    return int(m.group(1)) if m else 0


def classify_finding(issue, recommendation):
    issue_lower = (issue or "").lower()
    combined = f"{issue} {recommendation}".lower()
    issue_amounts = extract_money_amounts(issue)
    issue_amount = max(issue_amounts) if issue_amounts else None

    if "overage" in issue_lower:
        if issue_amount is not None and issue_amount < 1000:
            return "Immaterial Findings 3"
        return "Cash/Fund/Collection Overage (₱1,000.00 and above) -4"

    if "shortage" in issue_lower:
        if "no cash shortage" in issue_lower:
            return "No Findings 10"
        if issue_amount is not None and issue_amount < 1000:
            return "Immaterial Findings 3"
        if issue_amount is not None and issue_amount < 3000:
            return "Cash/Fund/Collection Shortage (below ₱3,000.00) -4"
        return "Cash/Fund/Collection Shortage (₱3,000.00 and above) -8"

    if "no findings" in combined or "no cash shortage" in combined or "neither shortage nor overage" in combined:
        return "No Findings 10"
    if "immaterial" in combined:
        return "Immaterial Findings 3"

    if any(w in combined for w in ["policy", "policies", "procedure", "procedures", "guidelines", "sop"]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    doc_terms = ["pcv", "voucher", "receipt information", "incomplete receipt", "incorrect receipt",
                 "missing", "document", "signature", "transmittal", "form", "cv information",
                 "monitoring", "mixing"]
    if any(t in combined for t in doc_terms):
        return "Ignore or Disregard Office/Operation Best Practices -3"

    return "Ignore or Disregard Office/Operation Best Practices -3"


def get_report_body(text):
    t = (text or "").replace("\r", "\n")

    start = 0

    patterns = [
        r"Issue\s*No\..*?Audit Findings.*?Recommendation",
        r"Audit Findings.*?Recommendation",
        r"Issue\s*No\."
    ]

    for pat in patterns:
        m = re.search(pat, t, re.I | re.S)
        if m:
            start = m.end()
            break

    end = len(t)

    for marker in [
        "Prepared/Audited by",
        "Prepared by",
        "Reviewed by",
        "Noted by",
        "cc:",
        "EXHIBIT A",
        "EXHIBIT B",
        "Request for Soft Copy"
    ]:
        pos = t.find(marker, start)
        if pos > 0:
            end = min(end, pos)

    return t[start:end]


def extract_recommendations(block):
    patterns = [
        r"(We recommend(?: that)?\s+.+?)(?=\n\s*\d+\.|\n[A-Z][A-Z /&()-]{5,}:|\nAction Taken:|\nPrepared|\Z)",
        r"(Please review\s+.+?)(?=\n\s*\d+\.|\n[A-Z][A-Z /&()-]{5,}:|\nAction Taken:|\nPrepared|\Z)",
        r"(We advise\s+.+?)(?=\n\s*\d+\.|\n[A-Z][A-Z /&()-]{5,}:|\nAction Taken:|\nPrepared|\Z)",
    ]
    rec = ""
    for pat in patterns:
        m = re.search(pat, block, re.I | re.S)
        if m:
            rec = clean_text(m.group(1))
            break
    if not rec or rec.upper() in ["NONE", "N/A"]:
        return "None", "None"
    rec = rec.replace("We recommend that ", "").replace("We recommend ", "").strip()
    return (rec[0].upper() + rec[1:] if rec else rec), "None"


def extract_explanation(block):
    pats = [
        r"((?:Mr\.|Ms\.)\s+[A-Z][A-Za-z .]+?\s+(?:claimed|explained|stated).+?)(?=We recommend|Please review|We advise|Action Taken:|\Z)",
        r"((?:According to|As per)\s+.+?)(?=We recommend|Please review|We advise|Action Taken:|\Z)"
    ]
    for pat in pats:
        m = re.search(pat, block, re.I | re.S)
        if m:
            return clean_text(m.group(1))
    return "None"


def extract_correction(block):
    m = re.search(r"Action Taken\s*:\s*(.+?)(?=\n\s*\d+\.|\nPrepared|\nReviewed|\nNoted|\Z)", block, re.I | re.S)
    if not m:
        return "None"
    value = clean_text(m.group(1))
    if not value or value.upper() in ["NONE", "N/A", "NO ACTION TAKEN"]:
        return "None"
    return value


def make_issue_summary(issue, block):
    combined_text = f"{issue} {block}"
    combined = combined_text.lower()
    amounts = extract_money_amounts(issue) or extract_money_amounts(combined_text)
    amount = max(amounts) if amounts else None

    if "overage" in combined:
        if "unrecorded receipt" in combined and amount is not None:
            return f"Cash overage of ₱{amount:,.2f} due to unrecorded receipt."
        if amount is not None:
            return f"Cash overage of ₱{amount:,.2f} was noted."
        return "Cash overage was noted."
    if "shortage" in combined:
        if amount is not None:
            return f"Cash shortage of ₱{amount:,.2f} was noted."
        return "Cash shortage was noted."
    if "late preparation" in combined and "pcv" in combined:
        return "Delayed preparation of PCV."
    if "outdated monitoring" in combined or "monitoring" in combined:
        return "Monitoring records were not updated regularly."
    if "mixing" in combined:
        return "Petty cash and revolving fund were maintained under a single record."
    if "pcv" in combined:
        return "Petty cash voucher documentation issue was noted."
    return "Issue noted during audit review."


def split_findings(text):
    body = get_report_body(text).replace("\r", "\n")

    st.subheader("BODY DEBUG")
    st.code(body[:5000])

    # Debug while testing only
    st.write("BODY DEBUG")
    st.text(body[:3000])

    matches = list(re.finditer(
        r"(?:^|\n)\s*(\d{1,2})\.\s*\n+([\s\S]*?)(?=(?:\n\s*\d{1,2}\.\s*\n)|$)",
        body,
        re.MULTILINE
    ))

    items = []

    for idx, m in enumerate(matches):
        issue_no = m.group(1)
        block_text = m.group(2)

        lines = [
            clean_text(x)
            for x in block_text.splitlines()
            if clean_text(x)
        ]

        if not lines:
            continue

        raw_title = lines[0].strip(":")

        false_terms = [
            "TO :", "FROM :", "RE :", "DATE :", "REF :",
            "AUDITEE NAME", "POSITION :", "COMPANY/DEPT",
            "PERIOD DATE", "SCOPE :", "OBJECTIVE"
        ]

        if any(term.replace(" ", "").lower() in raw_title.replace(" ", "").lower() for term in false_terms):
            continue

        block = "\n".join(lines[1:])

        rec1, rec2 = extract_recommendations(block)

        items.append({
            "issue_no": issue_no,
            "issue": raw_title,
            "block": block,
            "recommendation1": rec1,
            "recommendation2": rec2,
            "explanation": extract_explanation(block),
            "correction": extract_correction(block),
        })

    return items

def filter_no_findings_when_other_issues(items):
    actual = []
    no_findings = []
    for item in items:
        text = (item["issue"] + " " + item.get("block", "")).upper()
        is_no = "NO CASH SHORTAGE" in text or "NO FINDINGS" in text or "NEITHER SHORTAGE NOR OVERAGE" in text
        if is_no:
            no_findings.append(item)
        else:
            actual.append(item)
    return actual if actual else items


def load_masterlist(uploaded):
    if uploaded is None:
        return None
    if uploaded.name.lower().endswith(".csv"):
        return pd.read_csv(uploaded)
    return pd.read_excel(uploaded)


def find_column(df, candidates):
    if df is None or df.empty:
        return None
    for c in df.columns:
        lower = clean_text(c).lower()
        if any(x in lower for x in candidates):
            return c
    return None


def match_employee(master_df, auditee_name):
    if master_df is None or master_df.empty:
        return "None", auditee_name
    name_col = find_column(master_df, ["full name", "employee name", "name"])
    id_col = find_column(master_df, ["employee id", "employee no", "id no", "id"])
    if not name_col:
        return "None", auditee_name

    words = [w.lower() for w in re.sub(r"[^A-Za-zñÑ ]", " ", auditee_name).split() if len(w) > 1]
    tokens = [words[0], words[-1]] if len(words) >= 2 else words

    best, best_score = None, -1
    for _, row in master_df.iterrows():
        full_name = clean_text(row.get(name_col, ""))
        score = sum(1 for t in tokens if t in full_name.lower())
        if len(tokens) >= 2 and all(t in full_name.lower() for t in tokens):
            score += 2
        if score > best_score:
            best, best_score = row, score

    if best is not None and best_score >= 2:
        return clean_text(best.get(id_col, "None")) if id_col else "None", clean_text(best.get(name_col, auditee_name))
    return "None", auditee_name


def prepared_by_auditor(text):
    m = re.search(r"Prepared(?:/Audited)? by\s*:\s*(.+?)(?:Reviewed by|Noted by|cc:|Audit/file|$)", text, re.I | re.S)
    area = m.group(1).upper() if m else ""
    for auditor in AUDITORS:
        toks = [t.upper() for t in auditor.split() if len(t) > 2]
        if toks and toks[0] in area and toks[-1].replace(".", "") in area.replace(".", ""):
            return auditor
    if "SARINA" in area and "AMURAW" in area:
        return "Sarina Amuraw"
    if "PATRICIA" in area and "DEL ROSARIO" in area:
        return "Patricia Anne Del Rosario"
    return "None"


def classify_audit_type(text):
    lower = text.lower()
    sales_terms = ["area sales representative", "district sales supervisor", "regional sales supervisor", "technical sales supervisor", "sales personnel"]
    return "Operations Audit" if any(t in lower for t in sales_terms) else "Financial Audit"


def save_pdf_cloud(uploaded_file, header):
    supabase = get_supabase()
    if supabase is None:
        return None, "Cloud not configured"
    bucket = os.getenv("SUPABASE_BUCKET", "audit-pdfs")
    audit_ref = header.get("audit_reference", "None")
    auditee = header.get("auditee_name", "None")
    filename = f"{audit_ref}_{auditee}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)

    uploaded_file.seek(0)
    content = uploaded_file.read()
    uploaded_file.seek(0)

    supabase.storage.from_(bucket).upload(filename, content, {"content-type": "application/pdf"})
    return filename, bucket


def save_to_database(report, records_df, pdf_path, bucket):
    supabase = get_supabase()
    if supabase is None:
        return

    report_payload = {
        "encoded_date": date.today().isoformat(),
        "audit_reference": report["audit_reference"],
        "date_reported": report["date_reported"],
        "auditee_name": report["auditee_name"],
        "scope_date": report["scope_date"],
        "year": report["year"],
        "pdf_path": pdf_path,
        "pdf_bucket": bucket,
    }
    res = supabase.table("audit_reports").insert(report_payload).execute()
    report_id = res.data[0]["id"] if res.data else None

    payload = []
    for _, r in records_df.iterrows():
        item = {str(k).lower().replace(" ", "_").replace("#", "row_no").replace("/", "_"): (None if pd.isna(v) else v) for k, v in r.to_dict().items()}
        item["report_id"] = report_id
        payload.append(item)
    if payload:
        supabase.table("audit_findings").insert(payload).execute()


def load_archive_from_database(ref_filter="", auditee_filter=""):
    supabase = get_supabase()
    if supabase is None:
        return pd.DataFrame()
    query = supabase.table("audit_reports").select("*").order("created_at", desc=True)
    if ref_filter:
        query = query.ilike("audit_reference", f"%{ref_filter}%")
    if auditee_filter:
        query = query.ilike("auditee_name", f"%{auditee_filter}%")
    res = query.execute()
    return pd.DataFrame(res.data)


def build_rows(text, master_df, manual_df):
    header = extract_header(text)
    emp_id, emp_name = match_employee(master_df, header["auditee_name"])
    auditor_default = prepared_by_auditor(text)
    audit_type = classify_audit_type(text)
    items = filter_no_findings_when_other_issues(split_findings(text))
    st.write("DEBUG ITEMS:", items)

    manual_map = {}
    if manual_df is not None and not manual_df.empty:
        for _, r in manual_df.iterrows():
            if clean_text(r.get("Issue No.", "")):
                manual_map[clean_text(r.get("Issue No.", ""))] = r

    rows = []
    for row_no, item in enumerate(items, 1):
        manual = manual_map.get(item["issue_no"])
        task_id = header["task_id"]
        auditor = auditor_default
        reaction = ""
        frequency = ""

        if manual is not None:
            task_id = clean_text(manual.get("Task ID", "")) or task_id
            auditor = clean_text(manual.get("Auditor", "")) or auditor
            reaction = clean_text(manual.get("Reaction", ""))
            frequency = clean_text(manual.get("Frequency", ""))

        findings = classify_finding(item["issue"], item["recommendation1"])
        score = parse_score(findings)
        if "No Findings" in findings or "Immaterial Findings" in findings:
            reaction = "Maintaining Status Quo"
            frequency = "Not Applicable"

        improve = RESPONSE_RATE.get(reaction, 0) * FREQUENCY_RATE.get(frequency, 1)
        net = score + improve
        case_status = "No Case/Issue" if ("No Findings" in findings or "Immaterial Findings" in findings) else "Follow-up with HR"
        user = auditor.split()[0] if auditor and auditor != "None" else "None"

        rows.append([
            row_no, date.today().isoformat(), audit_type, header["date_reported"],
            header["audit_reference"], emp_id, emp_name, task_id or "None",
            header["scope_date"], header["year"], findings,
            make_issue_summary(item["issue"], item["block"]),
            item["explanation"] or "None",
            item["recommendation1"] or "None",
            item["recommendation2"] or "None",
            auditor or "None", "None", reaction, frequency,
            item["correction"] or "None", "", case_status, score, improve, net,
            "Individual", user
        ])
    return pd.DataFrame(rows, columns=HEADERS), header, items


def excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Audit Extraction")
    return output.getvalue()


st.title(f"{SYSTEM_NAME} ({SYSTEM_SHORT})")
st.caption("Cloud-ready audit report extraction, storage, archive, and findings database.")

if cloud_enabled():
    st.success("Cloud mode enabled: Supabase database/storage configured.")
else:
    st.warning("Cloud mode not configured. Add Supabase secrets/env variables before deployment.")

with st.sidebar:
    st.header("Modules")
    page = st.radio("Go to", ["Dashboard", "Upload Report", "PDF Archive", "Findings Database", "Employee Masterlist"])
    st.divider()
    ref_filter = st.text_input("Filter by Reference No.")
    auditee_filter = st.text_input("Filter by Auditee Name")

if page == "Dashboard":
    st.subheader("Dashboard")
    archive_df = load_archive_from_database(ref_filter, auditee_filter) if cloud_enabled() else pd.DataFrame()
    if archive_df.empty:
        st.info("No cloud records yet, or Supabase is not configured.")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Reports", len(archive_df))
        c2.metric("Years Covered", archive_df["year"].nunique() if "year" in archive_df else 0)
        c3.metric("Filtered Results", len(archive_df))
        st.dataframe(archive_df, use_container_width=True)

elif page == "Upload Report":
    st.subheader("Upload Audit Report")
    master_file = st.file_uploader("Upload Employee Masterlist", type=["xlsx", "csv"])
    pdf_file = st.file_uploader("Upload Audit Report PDF", type=["pdf"])

    master_df = load_masterlist(master_file) if master_file else None
    if master_df is not None:
        st.dataframe(master_df.head(20), use_container_width=True)

    if pdf_file:
        raw_text = extract_pdf_text(pdf_file)
        with st.expander("Show / edit extracted text"):
            edited_text = st.text_area("Extracted text", raw_text, height=300)

        prelim = filter_no_findings_when_other_issues(split_findings(edited_text))
        manual_df = pd.DataFrame([{
            "Issue No.": x["issue_no"],
            "Detected Issue": x["issue"],
            "Task ID": "",
            "Auditor": "",
            "Reaction": "",
            "Frequency": "",
        } for x in prelim])

        edited_manual = st.data_editor(
            manual_df,
            use_container_width=True,
            column_config={
                "Auditor": st.column_config.SelectboxColumn("Auditor", options=[""] + AUDITORS),
                "Reaction": st.column_config.SelectboxColumn("Reaction", options=REACTION_OPTIONS),
                "Frequency": st.column_config.SelectboxColumn("Frequency", options=FREQUENCY_OPTIONS),
            }
        )

        if st.button("Generate Extraction", type="primary"):
            result_df, header, items = build_rows(edited_text, master_df, edited_manual)
            st.json(header)
            edited_result = st.data_editor(
                result_df,
                use_container_width=True,
                column_config={
                    "Findings": st.column_config.SelectboxColumn("Findings", options=FINDINGS_DROPDOWN),
                    "Reaction": st.column_config.SelectboxColumn("Reaction", options=REACTION_OPTIONS),
                    "Frequency": st.column_config.SelectboxColumn("Frequency", options=FREQUENCY_OPTIONS),
                }
            )

            st.download_button(
                "Download Excel Output",
                data=excel_bytes(edited_result),
                file_name="audit_extraction_output.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

            if cloud_enabled():
                if st.button("Save PDF and Findings to Cloud"):
                    pdf_path, bucket = save_pdf_cloud(pdf_file, header)
                    save_to_database(header, edited_result, pdf_path, bucket)
                    st.success("Saved to cloud database and PDF storage.")

elif page == "PDF Archive":
    st.subheader("PDF Archive")
    df = load_archive_from_database(ref_filter, auditee_filter) if cloud_enabled() else pd.DataFrame()
    if df.empty:
        st.info("No archive records found.")
    else:
        st.dataframe(df, use_container_width=True)

elif page == "Findings Database":
    st.subheader("Findings Database")
    if cloud_enabled():
        supabase = get_supabase()
        res = supabase.table("audit_findings").select("*").limit(500).execute()
        st.dataframe(pd.DataFrame(res.data), use_container_width=True)
    else:
        st.info("Configure Supabase to use this module.")

elif page == "Employee Masterlist":
    st.subheader("Employee Masterlist")
    st.info("In the cloud version, employee masterlist should be stored in Supabase table: employee_masterlist.")
