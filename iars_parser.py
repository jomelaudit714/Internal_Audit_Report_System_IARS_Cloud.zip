
import re
from datetime import date
import pandas as pd
import pdfplumber

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

RESPONSE_RATE = {
    "Maintaining Status Quo": 1,
    "Do Some Adjustment": 0,
    "Performed SAME offense": -3,
    "": 0,
    "None": 0,
}

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

    "Damaged and/or Lost Stocks Due To Negligence (₱3,000.00 and above) -10",
    "Damaged and/or Lost Stocks Due To Negligence (below ₱3,000.00) -3",

    "SOTEX and/or Expired Issues (₱3,000.00 and above) -4",
    "SOTEX and/or Expired Issues (below ₱3,000.00) -2",

    "Additional Credit Term With Overdue / Giving Credit Terms To Non-Credit Customer -7",

    "Omission & Alteration Of Details in Documents -7",

    "Turn Over Sales -10",

    "Stock Pull-Out -10",

    "Possession and/or Peddling Non-EDL Products -10",

    "Denied Invoices (DR, PR & SI) -10",

    "Issuance Of Unofficial/Fabricated Documents -10",

    "Uncooperative or Failed To Produce Documents/Results Within Reasonable Time -4",

    "Unavailable or Unreliable Inventory Records -6",

    "Missing, Misused or Lost Of Documents/Asset(s) -3",

    "Material Inventory Shortage (₱3,000.00 and above) -5",

    "Material Inventory Shortage (below ₱3,000.00) -3",

    "Material Inventory Overage (Variance) -2",

    "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4",

    "Ignore or Disregard Office/Operation Best Practices -3",

    "Manipulate To Deceive or Defraud For Personal Gain -10",

    "Unethical Act or Behavior -6",

    "Unobservant / Failure To Follow Instructed Procedures -2",

    "Unauthorized Use of Asset(s) -2",

    "Delivery and/or Computation, Reporting Error(s) -2",

    "Immaterial Findings 3",

    "No Findings 10"

]

REACTION_OPTIONS = [
    "", "Maintaining Status Quo", "Do Some Adjustment", "Performed SAME offense",
    "Complied with previous recommendation", "Established guidelines",
    "Acknowledged the issue & will do correction", "Diverted the issue",
    "Low priority", "Undertake unfavorable approach", "Uncooperative",
]

FREQUENCY_OPTIONS = [
    "", "Not Applicable", "First Time", "Second Time", "Third Time",
    "Fourth Time", "Fifth Time", "Sixth Time", "Seventh Time",
]

def clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()

def clean_cell_preserve(value):
    if value is None:
        return ""
    lines = [clean_text(x) for x in str(value).replace("\r", "\n").split("\n")]
    return "\n".join([x for x in lines if x])

def find_after_label(text, labels):
    if isinstance(labels, str):
        labels = [labels]
    for label in labels:
        m = re.search(rf"{re.escape(label)}\s*[:\-]\s*([^\n\r]+)", text or "", re.I)
        if m:
            return clean_text(m.group(1))
    return "None"

def extract_all_text(pdf_file):
    with pdfplumber.open(pdf_file) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)

def extract_header(text):
    date_reported = find_after_label(text, "DATE")
    audit_reference = find_after_label(text, "REF")
    auditee_name = find_after_label(text, "AUDITEE NAME")
    period = find_after_label(text, ["PERIOD DATE", "COVERING PERIOD", "SCOPE DATE"])
    task_id = find_after_label(text, "TASK ID")
    company = find_after_label(text, ["COMPANY/DEPT.", "COMPANY/DEPT", "COMPANY"])
    audit_title = find_after_label(text, ["RE"])

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
        "company": company,
        "audit_title": audit_title,
    }

def prepared_by_auditor(text):
    m = re.search(
        r"Prepared(?:/Audited)? by\s*:\s*(.+?)(?:Reviewed by|Noted by|cc:|Audit/file|$)",
        text,
        re.I | re.S
    )
    area = (m.group(1) if m else "").upper()

    candidates = []
    for auditor in AUDITORS:
        words = [w for w in re.sub(r"[^A-Za-z ]", " ", auditor).upper().split() if len(w) > 2]
        if words and words[0] in area and words[-1] in area:
            candidates.append((area.find(words[0]), auditor))
    if candidates:
        return sorted(candidates)[0][1]
    return "None"

def extract_money_amounts(value):
    amounts = []
    for m in re.finditer(r"(?:₱|P)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2}))", value or "", re.I):
        try:
            amounts.append(float(m.group(1).replace(",", "")))
        except Exception:
            pass
    return amounts

def split_title_body(finding_text):
    lines = [clean_text(x) for x in (finding_text or "").splitlines() if clean_text(x)]
    title_lines, body_lines = [], []
    in_title = True

    for line in lines:
        norm = line.strip().rstrip(":")
        has_lower = any(ch.islower() for ch in norm)
        is_title = (not has_lower) or bool(re.match(r"^(CASH|STOCK|FUND|COLLECTION).*(OVERAGE|SHORTAGE)", norm, re.I))
        if in_title and is_title:
            title_lines.append(norm)
        else:
            in_title = False
            body_lines.append(line)

    if not title_lines and lines:
        title_lines = [lines[0].rstrip(":")]
        body_lines = lines[1:]

    return clean_text(" ".join(title_lines)), "\n".join(body_lines)

def normalize_recommendation(rec):
    rec = clean_text(rec).replace("NONE.", "None").strip()
    if not rec or rec.upper() in ["NONE", "N/A", "NONE."]:
        return "None"

    rec = re.sub(r"^We recommend(?: that)?\s+", "", rec, flags=re.I)
    rec = re.sub(r"^We advise\s+", "", rec, flags=re.I)
    rec = re.sub(r"^Please review\s+", "Review ", rec, flags=re.I)

    # Convert "Ms. Name return..." to "Return..."
    rec = re.sub(
        r"^(Mr\.|Ms\.)\s+[A-Z][A-Za-z .]+?\s+(return|use|update|review|ensure|avoid)\b",
        lambda m: m.group(2).capitalize(),
        rec,
        flags=re.I
    )

    rec = re.sub(r"^The use of\s+(.+?)\s+as\b", r"Use \1 as", rec, flags=re.I)
    rec = re.sub(r"^Records be updated\b", "Update records", rec, flags=re.I)

    if rec:
        rec = rec[0].upper() + rec[1:]
    return rec

def remove_action_taken(text):
    return re.split(r"Action Taken\s*:", text or "", flags=re.I)[0]

def extract_correction_from_text(text):
    m = re.search(r"Action Taken\s*:\s*(.+)", text or "", re.I | re.S)
    if not m:
        return "None"
    val = clean_text(m.group(1))
    val = re.sub(r"\bPrepared(?:/Audited)? by:.*", "", val, flags=re.I | re.S)
    val = clean_text(val)
    if not val or val.upper() in ["NONE", "N/A", "NO ACTION TAKEN"]:
        return "None"
    return val

def extract_explanation_from_narrative(narrative):
    text = clean_text(remove_action_taken(narrative))
    text = re.sub(r"\(See Exhibit [A-Z]\)", "", text, flags=re.I)

    patterns = [
        r"((?:Mr\.|Ms\.)\s+[A-Z][A-Za-z .]+?\s+(?:claimed|explained|stated)\s+.+)",
        r"((?:According to|As per)\s+.+)",
        r"((?:He|She|They)\s+(?:claimed|explained|stated)\s+.+)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return clean_text(m.group(1))
    return "None"

def make_issue_summary(issue, narrative):
    combined = clean_text(issue + " " + narrative).lower()
    issue_clean = clean_text(issue)
    
    no_finding_patterns = [
        "no cash shortage",
        "no cash overage",
        "no cash shortage/overage",
        "no cash overage/shortage",
        "no cash shortage or overage",
        "no cash overage or shortage",
        "no shortage/overage",
        "no overage/shortage",
        "fund is intact",
        "cash count tallied",
        "cash count matched",
        "cash counted matched",
        "no discrepancy noted",
        "no variance noted",
        "no findings"
    ]

    if any(p in combined for p in no_finding_patterns):
        return "No cash shortage or overage was noted."
    
    amounts = extract_money_amounts(issue) or extract_money_amounts(narrative)
    amount = max(amounts) if amounts else None

    # Monetary / cash / stock issues
    if "cash" in combined or "fund" in combined or "collection" in combined or "sales" in combined:
        if "overage" in combined:
            if "unrecorded receipt" in combined and amount is not None:
                return f"Cash overage of ₱{amount:,.2f} due to unrecorded receipt."
            if amount is not None:
                return f"Cash/Fund/Collection overage of ₱{amount:,.2f} was noted."
            return "Cash/Fund/Collection overage was noted."

        if "shortage" in combined:
            if amount is not None:
                return f"Cash/Fund/Collection shortage of ₱{amount:,.2f} was noted."
            return "Cash/Fund/Collection shortage was noted."

    if "stock" in combined or "inventory" in combined:
        if "overage" in combined:
            if amount is not None:
                return f"Stock/Inventory overage of ₱{amount:,.2f} was noted."
            return "Stock/Inventory overage was noted."

        if "shortage" in combined:
            if amount is not None:
                return f"Stock/Inventory shortage of ₱{amount:,.2f} was noted."
            return "Stock/Inventory shortage was noted."

    # Specific category summaries
    if "non-remittance" in combined or "unremitted" in combined or "not remitted" in combined:
        return "Collection was not remitted within the required period."

    if "delayed deposit" in combined or "late deposit" in combined:
        return "Deposit of collections or funds was delayed."

    if "late issuance" in combined or "non-issuance" in combined or "no receipt" in combined:
        return "Receipt was issued late or was not issued."

    if "omission" in combined or "alteration" in combined:
        return "Document details were omitted or altered."

    if "pcv" in combined:
        if "late preparation" in combined:
            return "Delayed preparation of PCV."
        return "Petty cash voucher documentation issue was noted."

    if "receipt information" in combined or "incomplete receipt" in combined or "incorrect receipt" in combined:
        return "Receipt information was incomplete or incorrect."

    if "unavailable inventory" in combined or "unreliable inventory" in combined:
        return "Inventory records were unavailable or unreliable."

    if "missing" in combined and ("document" in combined or "asset" in combined):
        return "Document or asset was missing."

    if "misused" in combined and ("document" in combined or "asset" in combined):
        return "Document or asset was misused."

    if "lost" in combined and ("document" in combined or "asset" in combined):
        return "Document or asset was lost."

    if "unauthorized use" in combined and "asset" in combined:
        return "Company asset was used without proper authorization."

    if "delivery error" in combined:
        return "Delivery error was noted."

    if "computation error" in combined:
        return "Computation error was noted."

    if "reporting error" in combined:
        return "Reporting error was noted."

    if "uncooperative" in combined:
        return "Auditee was uncooperative or failed to provide required documents/results."

    if "unethical" in combined:
        return "Unethical act or behavior was noted."

    if "manipulate" in combined or "deceive" in combined or "defraud" in combined:
        return "Manipulation, deception, or fraudulent act was noted."

    if "outdated monitoring" in combined or "outdated records" in combined or "outdated recording" in combined:
        return "Monitoring or records were not updated."

    if "monitoring" in combined:
        return "Monitoring weakness was noted."

    if "mixing" in combined:
        return "Petty cash and revolving fund were maintained under a single record."

    if "policy" in combined or "procedure" in combined or "guideline" in combined or "sop" in combined:
        return "Nonconformity with written policy, procedure, guideline, or process was noted."

    if "failure to follow" in combined or "failed to follow" in combined:
        return "Failure to follow instructed procedure was noted."

    if "no cash shortage" in combined or "no findings" in combined:
        return "No cash shortage, overage, or audit exception was noted."

    if "immaterial" in combined:
        return "Immaterial finding with minimal impact was noted."

    # Final fallback based on issue title
    if issue_clean:
        return f"{issue_clean} was noted."

    return "Issue noted during audit review."
    
def classify_finding(issue, recommendation, narrative=""):
    issue_lower = clean_text(issue).lower()
    rec_lower = clean_text(recommendation).lower()
    narrative_lower = clean_text(narrative).lower()

    combined = f"{issue_lower} {narrative_lower} {rec_lower}"

    no_finding_patterns = [
        "no cash shortage",
        "no cash overage",
        "no cash shortage/overage",
        "no cash overage/shortage",
        "no cash shortage or overage",
        "no cash overage or shortage",
        "no shortage/overage",
        "no overage/shortage",
        "fund is intact",
        "cash count tallied",
        "cash count matched",
        "cash counted matched",
        "no discrepancy noted",
        "no variance noted",
        "no findings"
    ]

    if any(p in combined for p in no_finding_patterns):
        return "No Findings 10"

    amounts = extract_money_amounts(issue) or extract_money_amounts(narrative)
    amount = max(amounts) if amounts else None

    is_estancia = "estancia de lorenzo" in combined
    is_petty_cash = "petty cash" in combined

    # Monetary classifications
    if "cash shortage" in issue_lower or "fund shortage" in issue_lower or "collection shortage" in issue_lower:
        if amount is not None and amount < 3000:
            return "Cash/Fund/Collection Shortage (below ₱3,000.00) -4"
        return "Cash/Fund/Collection Shortage (₱3,000.00 and above) -8"

    if "cash overage" in issue_lower or "fund overage" in issue_lower or "collection overage" in issue_lower:
        if amount is not None and amount < 1000:
            return "Cash/Fund/Collection Overage (below ₱1,000.00) -2"
        return "Cash/Fund/Collection Overage (₱1,000.00 and above) -4"

    # Petty Cash / Estancia stricter rules
    if is_estancia and any(k in combined for k in [
        "policy", "procedure", "proper procedure", "guidelines", "sop",
        "required", "must", "should be supported", "cash voucher"
    ]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    if is_petty_cash and any(k in combined for k in [
        "reimbursement exceeding", "without stamped paid", "unsupported",
        "cash voucher", "official receipt", "invoice"
    ]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    # Issue title-driven classifications
    if any(k in issue_lower for k in [
        "incomplete details", "incomplete receipt", "incorrect receipt",
        "incomplete cv", "incomplete pcv", "incorrect pcv",
        "omission", "alteration"
    ]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "required"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        if any(k in combined for k in ["missing", "no signature", "no date", "incorrect date", "no supplier", "no owner"]):
            return "Omission & Alteration Of Details in Documents -7"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in [
        "late preparation of pcv", "no preparation of pcv", "uncancelled pcv",
        "inconsistent using of pcv"
    ]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "required"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in [
        "no document used", "undocumented", "without document"
    ]):
        return "Missing, Misused or Lost Of Documents/Asset(s) -3"

    if any(k in issue_lower for k in [
        "inaccurate monitoring", "outdated monitoring", "no daily balancing",
        "no monitoring", "incomplete monitoring", "delayed recording"
    ]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "proper procedure"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in [
        "depleted fund", "low fund", "fund depletion"
    ]):
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in [
        "mixing of fund", "mixed fund", "personal cash", "outside its purpose"
    ]):
        return "Ignore or Disregard Office/Operation Best Practices -3"

    # Policy / procedure override
    if any(k in combined for k in [
        "nonconformity", "non-compliance", "not following proper procedure",
        "policy", "policies", "procedure", "procedures", "guidelines",
        "sop", "process", "memorandum", "written requirement"
    ]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    if "uncooperative" in combined:
        return "Uncooperative or Failed To Produce Documents/Results Within Reasonable Time -4"

    if "immaterial" in combined:
        return "Immaterial Findings 3"

    return "Ignore or Disregard Office/Operation Best Practices -3"
    
def detect_reaction(issue, narrative, recommendation):
    text = f"{issue} {narrative} {recommendation}".lower()

    if "uncooperative" in text:
        return "Uncooperative"

    if "same offense" in text or "same finding" in text or "previous audit" in text or "previously noted" in text:
        return "Performed SAME offense"

    if "complied with previous recommendation" in text:
        return "Complied with previous recommendation"

    if "established guidelines" in text:
        return "Established guidelines"

    if "acknowledged" in text:
        return "Acknowledged the issue & will do correction"

    return "Do Some Adjustment"

def detect_frequency(issue, narrative, recommendation):
    text = f"{issue} {narrative} {recommendation}".lower()

    prior_count = 0

    prior_count += len(re.findall(r"previous audit", text))
    prior_count += len(re.findall(r"previously noted", text))
    prior_count += len(re.findall(r"same finding was noted", text))
    prior_count += len(re.findall(r"reference no\.", text))
    prior_count += len(re.findall(r"\b20\d{2}iad\d+\b", text))

    if prior_count <= 0:
        return "First Time"

    occurrence = prior_count + 1

    if occurrence == 2:
        return "Second Time"
    if occurrence == 3:
        return "Third Time"
    if occurrence == 4:
        return "Fourth Time"
    if occurrence == 5:
        return "Fifth Time"
    if occurrence == 6:
        return "Sixth Time"

    return "Seventh Time"

def parse_score(findings):
    m = re.search(r"(-?\d+)\s*$", findings or "")
    return int(m.group(1)) if m else 0

def find_column(df, candidates):
    if df is None or df.empty:
        return None
    for c in df.columns:
        l = str(c).lower()
        if any(x in l for x in candidates):
            return c
    return None

def match_employee(master_df, auditee):
    if master_df is None or master_df.empty:
        return "None", auditee

    name_col = find_column(master_df, ["full name", "employee name", "name"])
    id_col = find_column(master_df, ["employee id", "employee no", "id no", "id"])
    if not name_col:
        return "None", auditee

    words = [w.lower() for w in re.sub(r"[^A-Za-zñÑ ]", " ", auditee).split() if len(w) > 1]
    tokens = [words[0], words[-1]] if len(words) >= 2 else words

    best, best_score = None, -1
    for _, r in master_df.iterrows():
        full = clean_text(r.get(name_col, ""))
        score = sum(1 for t in tokens if t in full.lower())
        if len(tokens) >= 2 and all(t in full.lower() for t in tokens):
            score += 2
        if score > best_score:
            best, best_score = r, score

    if best is not None and best_score >= 2:
        emp_id = clean_text(best.get(id_col, "None")) if id_col else "None"
        full_name = clean_text(best.get(name_col, auditee))
        return emp_id or "None", full_name or auditee

    return "None", auditee

def extract_finding_rows_from_pdf(pdf_file):
    rows = []

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue

                    cells = [clean_cell_preserve(c) for c in row]

                    issue_idx = None
                    issue_no = None
                    for i, c in enumerate(cells):
                        if re.fullmatch(r"\d{1,2}\.?", clean_text(c)):
                            issue_idx = i
                            issue_no = clean_text(c).rstrip(".")
                            break

                    if issue_idx is None:
                        continue

                    after = [c for c in cells[issue_idx + 1:] if clean_text(c)]
                    if not after:
                        continue

                    if len(after) >= 2:
                        finding_cell, rec_cell = after[-2], after[-1]
                    else:
                        finding_cell, rec_cell = after[0], ""

                    if "Audit Findings" in finding_cell or clean_text(finding_cell).lower() == "no.":
                        continue

                    issue, narrative = split_title_body(finding_cell)
                    if not issue:
                        continue

                    recommendation = normalize_recommendation(rec_cell)
                    correction = extract_correction_from_text(narrative)
                    narrative_no_action = remove_action_taken(narrative)

                    rows.append({
                        "issue_no": issue_no,
                        "issue": issue,
                        "narrative": narrative_no_action,
                        "recommendation1": recommendation,
                        "recommendation2": "None",
                        "explanation": extract_explanation_from_narrative(narrative),
                        "correction": correction,
                    })

    return rows

def filter_no_findings_when_other_issues(items):
    actual, no_findings = [], []
    for item in items:
        text = item["issue"].upper()
        if "NO CASH SHORTAGE" in text or "NO FINDINGS" in text:
            no_findings.append(item)
        else:
            actual.append(item)
    return actual if actual else items

def classify_audit_type(text):
    sales_terms = [
        "area sales representative", "district sales supervisor",
        "regional sales supervisor", "technical sales supervisor", "sales personnel"
    ]
    return "Operations Audit" if any(t in text.lower() for t in sales_terms) else "Financial Audit"

def build_records(pdf_file, master_df=None, manual_df=None):
    text = extract_all_text(pdf_file)
    header = extract_header(text)
    emp_id, emp_name = match_employee(master_df, header["auditee_name"])
    auditor_default = prepared_by_auditor(text)
    audit_type = classify_audit_type(text)

    items = filter_no_findings_when_other_issues(extract_finding_rows_from_pdf(pdf_file))

    manual_map = {}
    if manual_df is not None and not manual_df.empty:
        for _, r in manual_df.iterrows():
            issue_no = clean_text(r.get("Issue No.", ""))
            if issue_no:
                manual_map[issue_no] = r

    rows = []
    for row_no, item in enumerate(items, 1):
        manual = manual_map.get(item["issue_no"])
        task_id = header["task_id"]
        auditor = auditor_default

        reaction = detect_reaction(
            item["issue"],
            item["narrative"],
            item["recommendation1"]
        )

        frequency = detect_frequency(
            item["issue"],
            item["narrative"],
            item["recommendation1"]
        )    

        if manual is not None:
            task_id = clean_text(manual.get("Task ID", "")) or task_id
            auditor = clean_text(manual.get("Auditor", "")) or auditor
            reaction = clean_text(manual.get("Reaction", "")) or reaction
            frequency = clean_text(manual.get("Frequency", "")) or frequency

        findings = classify_finding(
            item["issue"],
            item["recommendation1"],
            item["narrative"]
        )
        
        score = parse_score(findings)

        if "No Findings" in findings or "Immaterial Findings" in findings:
            reaction = "Maintaining Status Quo"
            frequency = "Not Applicable"

        improve = RESPONSE_RATE.get(reaction, 0) * FREQUENCY_RATE.get(frequency, 1)
        net = score + improve
        case_status = "No Case/Issue" if ("No Findings" in findings or "Immaterial Findings" in findings) else "Follow-up with HR"
        user = auditor.split()[0] if auditor and auditor != "None" else "None"

        rows.append([
            row_no,
            date.today().isoformat(),
            audit_type,
            header["date_reported"],
            header["audit_reference"],
            emp_id,
            emp_name,
            task_id or "None",
            header["scope_date"],
            header["year"],
            findings,
            make_issue_summary(item["issue"], item["narrative"]),
            item["explanation"] or "None",
            item["recommendation1"] or "None",
            item["recommendation2"] or "None",
            auditor or "None",
            "None",
            reaction,
            frequency,
            item["correction"] or "None",
            "",
            case_status,
            score,
            improve,
            net,
            "Individual",
            user,
        ])

    return pd.DataFrame(rows, columns=HEADERS), header, items

def excel_bytes(df):
    from io import BytesIO
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Audit Extraction")
        ws = writer.book["Audit Extraction"]
        ws.freeze_panes = "A2"
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            cell.alignment = cell.alignment.copy(horizontal="center", vertical="center", wrap_text=True)
        widths = {
            "A":5,"B":14,"C":18,"D":18,"E":16,"F":14,"G":28,"H":12,"I":16,"J":10,
            "K":55,"L":60,"M":60,"N":60,"O":35,"P":28,"Q":14,"R":24,"S":18,
            "T":32,"U":12,"V":20,"W":10,"X":14,"Y":12,"Z":14,"AA":12
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = cell.alignment.copy(wrap_text=True, vertical="top")
    return output.getvalue()
