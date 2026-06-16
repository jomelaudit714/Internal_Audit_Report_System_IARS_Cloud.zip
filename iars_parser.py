import re
from datetime import date
from io import BytesIO
import pandas as pd
import pdfplumber

HEADERS = [
    "#", "Encoded Date", "Type", "Date Reported", "Audit Reference", "ID No", "Name",
    "Task ID", "Scope Date", "Year", "Findings", "Issue Detail Issue", "Explanation",
    "Recommendation1", "Recommendation2", "Audited By1", "Audited By2", "Reaction",
    "Frequency", "Correction", "Sanction", "Case Status", "Score", "Improve Score",
    "Net Score", "Audit Unit", "User"
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
    "Blanko 0",
    "Overage of Cash Collection -2",
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
    "No Findings 10",
]

REACTION_OPTIONS = [
    "", "Complied with previous recommendation", "Established guidelines",
    "Acknowledged the issue & will do correction", "Maintaining Status Quo",
    "Performed SAME offense", "Diverted the issue", "Low priority",
    "Undertake unfavorable approach", "Uncooperative", "Do Some Adjustment",
]

FREQUENCY_OPTIONS = [
    "", "Not Applicable", "First Time", "Second Time", "Third Time", "Fourth Time",
    "Fifth Time", "Sixth Time", "Seventh Time",
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

TITLE_KEYWORDS = [
    "SHORTAGE", "OVERAGE", "NO CASH", "PCV", "DOCUMENT", "MONITORING",
    "DEPLETED", "INCOMPLETE", "INCORRECT", "LATE", "UNCANCELLED",
    "UNREPLENISHED", "UNLIQUIDATED", "OUTSIDE ITS PURPOSE", "MIXING",
    "FUND", "DAILY BALANCING", "RECEIPT INFORMATION", "CASH ADVANCE",
    "CASH ADVANCES", "UNSUPPORTED", "BALANCING",
]

PRIORITY_TITLES = [
    "NO CASH SHORTAGE/OVERAGE",
    "NO CASH OVERAGE/SHORTAGE",
    "NO CASH SHORTAGE OR OVERAGE",
    "NO CASH OVERAGE OR SHORTAGE",
    "CASH SHORTAGE",
    "CASH OVERAGE",
    "NO PREPARATION OF PCV",
    "UNCANCELLED PCV",
    "NO DOCUMENT USED FOR CASH TAKEN FROM THE FUND",
    "INACCURATE MONITORING OF FUND",
    "OUTDATED MONITORING",
    "DEPLETED FUND",
    "INCOMPLETE RECEIPT INFORMATION",
    "INCORRECT RECEIPT INFORMATION",
    "LATE PREPARATION OF PCV",
    "INCONSISTENT USING OF PCV",
    "USE OF CASH ADVANCE OUTSIDE ITS PURPOSE",
    "INCOMPLETE DETAILS IN PCV",
    "INACCURATE PCV INFORMATION",
    "NO DAILY BALANCING / MONITORING OF FUND",
    "MIXING OF FUND WITH PERSONAL CASH OF CUSTODIAN",
    "MIXING OF PETTY CASH AND REVOLVING FUND",
]

NO_FINDING_PATTERNS = [
    "no cash shortage", "no cash overage", "no cash shortage/overage",
    "no cash overage/shortage", "no cash shortage or overage",
    "no cash overage or shortage", "no shortage/overage", "no overage/shortage",
    "no shortage or overage", "no overage or shortage", "fund is intact",
    "cash fund is intact", "revolving fund is intact", "petty cash fund is intact",
    "no variance noted", "no discrepancy noted", "cash count tallied",
    "cash count matched", "cash counted matched", "no findings",
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
    pdf_file.seek(0)
    with pdfplumber.open(pdf_file) as pdf:
        text = "\n".join((page.extract_text() or "") for page in pdf.pages)
    pdf_file.seek(0)
    return text.replace("\r", "\n")


def extract_header(text):
    date_reported = find_after_label(text, "DATE")
    audit_reference = find_after_label(text, "REF")
    auditee_name = find_after_label(text, "AUDITEE NAME")
    period = find_after_label(text, ["PERIOD DATE", "COVERING PERIOD", "SCOPE DATE"])
    company = find_after_label(text, ["COMPANY/DEPT.", "COMPANY/DEPT", "COMPANY"])
    audit_title = find_after_label(text, ["RE"])
    task_id = find_after_label(text, "TASK ID")

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
        re.I | re.S,
    )
    area = (m.group(1) if m else "").upper()
    candidates = []
    for auditor in AUDITORS:
        words = [w for w in re.sub(r"[^A-Za-z ]", " ", auditor).upper().split() if len(w) > 2]
        if words and words[0] in area and words[-1] in area:
            candidates.append((area.find(words[0]), auditor))
    return sorted(candidates)[0][1] if candidates else "None"


def extract_money_amounts(value):
    amounts = []
    for m in re.finditer(r"(?:₱|P)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2}))", value or "", re.I):
        try:
            amounts.append(float(m.group(1).replace(",", "")))
        except Exception:
            pass
    return amounts


def upper_ratio(text):
    letters = [c for c in clean_text(text) if c.isalpha()]
    if not letters:
        return 0
    return sum(1 for c in letters if c.isupper()) / len(letters)


def normalize_title(issue_title):
    title = clean_text(issue_title).strip().strip(":")
    upper = title.upper()
    for key in PRIORITY_TITLES:
        if key in upper:
            return clean_text(title[upper.find(key):])
    return title


def extract_title_prefix(line):
    """Return the bold/title text at the beginning of a PDF line, before recommendation text if merged."""
    s = clean_text(line).strip().strip(":")
    if not s:
        return ""

    m = re.search(r"\s+(?:We recommend|We advise|Please review|NONE\.?)\b", s, re.I)
    prefix = s[:m.start()].strip().rstrip(":") if m else s

    if len(prefix) > 180:
        return ""
    if upper_ratio(prefix) < 0.85:
        return ""
    if not any(k in prefix.upper() for k in TITLE_KEYWORDS):
        return ""
    if prefix.upper() in ["ISSUE", "NO", "NO.", "AUDIT FINDINGS", "RECOMMENDATION"]:
        return ""
    return prefix


def crop_report_body(text):
    m = re.search(r"Issue\s*\n(?:.*\n){0,5}?No\.", text, re.I)
    if m:
        text = text[m.end():]

    cut_positions = []
    for pat in [
        r"\n\s*Prepared/Audited by:",
        r"\n\s*Prepared by:",
        r"\n\s*Reviewed by:",
        r"\n\s*Noted by:",
        r"\n\s*cc:",
        r"\n\s*EXHIBIT\s+A",
        r"\n\s*Request for Soft Copy",
    ]:
        cm = re.search(pat, text, re.I)
        if cm:
            cut_positions.append(cm.start())
    if cut_positions:
        text = text[:min(cut_positions)]
    return text


def find_issue_title_entries(lines):
    entries = []
    i = 0
    while i < len(lines):
        first_title = extract_title_prefix(lines[i])
        if not first_title:
            i += 1
            continue

        start_i = i
        title_parts = [first_title]
        i += 1

        while i < len(lines):
            next_title = extract_title_prefix(lines[i])
            if next_title:
                title_parts.append(next_title)
                i += 1
            else:
                break

        entries.append({
            "start": start_i,
            "end_title": i,
            "title": normalize_title(" ".join(title_parts)),
        })
    return entries


def normalize_recommendation(rec):
    rec = clean_text(rec).replace("NONE.", "None").strip()
    rec = re.sub(r"^(?:of|to|the|be|no|not|as)\s+(?=(We recommend|We advise|Please review|Mr\.|Ms\.|The\s))", "", rec, flags=re.I)
    if not rec or rec.upper() in ["NONE", "N/A", "NONE."]:
        return "None"
    rec = re.sub(r"^We recommend(?: that)?\s+", "", rec, flags=re.I)
    rec = re.sub(r"^We advise\s+", "", rec, flags=re.I)
    rec = re.sub(r"^Please review\s+", "Review ", rec, flags=re.I)
    rec = re.sub(r"^(Mr\.|Ms\.)\s+[A-Z][A-Za-z .]+?\s+(return|use|update|review|ensure|avoid|explain)\b", lambda m: m.group(2).capitalize(), rec, flags=re.I)
    rec = re.sub(r"^The use of\s+(.+?)\s+as\b", r"Use \1 as", rec, flags=re.I)
    rec = re.sub(r"^Records be updated\b", "Update records", rec, flags=re.I)

    # Clean common right-column spill artifacts from PDF extraction.
    rec = re.sub(r"\bprevent\s+be\s+discrepancies\b", "prevent discrepancies", rec, flags=re.I)
    rec = re.sub(r"\b25%\s+not\s+utilization\b", "25% utilization", rec, flags=re.I)
    rec = re.sub(r"\bfund\s+as\s+depletion\b", "fund depletion", rec, flags=re.I)
    return rec[0].upper() + rec[1:] if rec else "None"


def remove_action_taken(text):
    return re.split(r"Action Taken\s*:", text or "", flags=re.I)[0]


def extract_correction_from_text(text):
    m = re.search(r"Action Taken\s*:\s*(.+)", text or "", re.I | re.S)
    if not m:
        return "None"
    val = clean_text(m.group(1))
    val = re.sub(r"\bPrepared(?:/Audited)? by:.*", "", val, flags=re.I | re.S)
    val = clean_text(val)
    return "None" if not val or val.upper() in ["NONE", "N/A", "NO ACTION TAKEN"] else val


def extract_explanation_from_narrative(narrative):
    text = clean_text(remove_action_taken(narrative))
    text = re.sub(r"\(See Exhibit [A-Z](?:\.\d+)?\)", "", text, flags=re.I)
    patterns = [
        r"((?:Mr\.|Ms\.)\s+[A-Z][A-Za-z .]+?\s+(?:claimed|explained|stated|admitted)\s+.+)",
        r"((?:According to|As per)\s+.+)",
        r"((?:He|She|They)\s+(?:claimed|explained|stated|admitted)\s+.+)",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return clean_text(m.group(1))
    return "None"


def make_issue_summary(issue, narrative):
    combined = clean_text(issue + " " + narrative).lower()
    issue_clean = clean_text(issue)
    if any(p in combined for p in NO_FINDING_PATTERNS):
        return "No cash shortage or overage was noted."

    amounts = extract_money_amounts(issue) or extract_money_amounts(narrative)
    amount = max(amounts) if amounts else None

    if any(x in combined for x in ["cash", "fund", "collection", "sales"]):
        if "overage" in issue.lower():
            return f"Cash/Fund/Collection overage of ₱{amount:,.2f} was noted." if amount else "Cash/Fund/Collection overage was noted."
        if "shortage" in issue.lower():
            return f"Cash/Fund/Collection shortage of ₱{amount:,.2f} was noted." if amount else "Cash/Fund/Collection shortage was noted."
    if "no preparation" in combined and "pcv" in combined:
        return "No PCV was prepared."
    if "late preparation" in combined and "pcv" in combined:
        return "Delayed preparation of PCV."
    if "uncancelled" in combined and "pcv" in combined:
        return "Uncancelled PCV was noted."
    if "no document used" in combined or "undocumented" in combined:
        return "Cash transaction was not properly documented."
    if "inaccurate monitoring" in combined or "outdated monitoring" in combined:
        return "Monitoring records were inaccurate or not updated."
    if "depleted fund" in combined:
        return "Fund was depleted below the expected utilization level."
    if "mixing" in combined:
        return "Petty cash and revolving fund were maintained under a single record."
    return f"{issue_clean} was noted." if issue_clean else "Issue noted during audit review."


def classify_finding(issue, recommendation, narrative="", company="", audit_title=""):
    issue_lower = clean_text(issue).lower()
    rec_lower = clean_text(recommendation).lower()
    narrative_lower = clean_text(narrative).lower()
    company_lower = clean_text(company).lower()
    audit_title_lower = clean_text(audit_title).lower()
    combined = f"{issue_lower} {narrative_lower} {rec_lower}"

    if any(p in combined for p in NO_FINDING_PATTERNS):
        return "No Findings 10"

    amounts = extract_money_amounts(issue) or extract_money_amounts(narrative)
    amount = max(amounts) if amounts else None
    is_estancia = "estancia de lorenzo" in company_lower
    is_petty_cash = "petty cash" in combined or "petty cash" in audit_title_lower

    if any(k in issue_lower for k in ["cash shortage", "fund shortage", "collection shortage"]):
        if amount is not None and amount < 1000:
            return "Immaterial Findings 3"
        if amount is not None and amount < 3000:
            return "Cash/Fund/Collection Shortage (below ₱3,000.00) -4"
        return "Cash/Fund/Collection Shortage (₱3,000.00 and above) -8"

    if any(k in issue_lower for k in ["cash overage", "fund overage", "collection overage"]):
        if amount is not None and amount < 1000:
            return "Cash/Fund/Collection Overage (below ₱1,000.00) -2"
        return "Cash/Fund/Collection Overage (₱1,000.00 and above) -4"

    if is_estancia and any(k in combined for k in ["policy", "procedure", "proper procedure", "guidelines", "sop", "required", "must", "cash voucher"]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    if is_petty_cash and any(k in combined for k in ["reimbursement exceeding", "without stamped paid", "unsupported", "cash voucher", "official receipt", "invoice"]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    if any(k in issue_lower for k in ["incomplete details", "incomplete receipt", "incorrect receipt", "incomplete cv", "incomplete pcv", "incorrect pcv", "omission", "alteration"]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "required"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        if any(k in combined for k in ["missing", "no signature", "no date", "incorrect date", "no supplier", "no owner"]):
            return "Omission & Alteration Of Details in Documents -7"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["late preparation of pcv", "no preparation of pcv", "uncancelled pcv", "inconsistent using of pcv"]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "required"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["no document used", "undocumented", "without document"]):
        return "Missing, Misused or Lost Of Documents/Asset(s) -3"

    if any(k in issue_lower for k in ["inaccurate monitoring", "outdated monitoring", "no daily balancing", "no monitoring", "incomplete monitoring", "delayed recording"]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "proper procedure"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["depleted fund", "low fund", "fund depletion", "mixing of fund", "mixed fund", "personal cash", "outside its purpose"]):
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in combined for k in ["nonconformity", "non-compliance", "not following proper procedure", "policy", "policies", "procedure", "procedures", "guidelines", "sop", "process", "memorandum", "written requirement"]):
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
    return ["Second Time", "Third Time", "Fourth Time", "Fifth Time", "Sixth Time", "Seventh Time"][min(prior_count - 1, 5)]


def parse_score(findings):
    m = re.search(r"(-?\d+)\s*$", findings or "")
    return int(m.group(1)) if m else 0


def find_column(df, candidates):
    if df is None or df.empty:
        return None
    for c in df.columns:
        lower = str(c).lower()
        if any(x in lower for x in candidates):
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


def extract_recommendation_from_segment(segment):
    m = re.search(r"(We recommend.+|We advise.+|Please review.+|NONE\.?)", segment, re.I | re.S)
    if not m:
        return "None"
    rec = m.group(1)
    rec = re.split(r"Action Taken\s*:", rec, flags=re.I)[0]
    return normalize_recommendation(rec)


def remove_title_from_segment(segment, title):
    result = segment
    for part in title.split():
        pass
    # Remove exact normalized title words when possible, but keep narrative if PDF interleaved columns.
    title_words = [re.escape(w) for w in clean_text(title).split()]
    if title_words:
        pat = r"\s*".join(title_words)
        result = re.sub(pat, "", result, count=1, flags=re.I).strip()
    return result


def extract_finding_rows_from_pdf(pdf_file):
    """
    Hybrid parser:
    - Uses PDF coordinates to keep Audit Findings (left column) separate from Recommendation (right column).
    - Uses bold/title-like lines in the left column as the issue title.
    - Does not rely on issue numbers because some PDFs do not extract the issue number as text.
    """
    rows = []
    pdf_file.seek(0)

    line_rows = []
    x_cut = 395

    with pdfplumber.open(pdf_file) as pdf:
        for page_no, page in enumerate(pdf.pages, 1):
            words = page.extract_words(x_tolerance=2, y_tolerance=3, keep_blank_chars=False) or []
            grouped = {}
            for w in words:
                key = round(w.get("doctop", w["top"]) / 3) * 3
                grouped.setdefault(key, []).append(w)

            for key in sorted(grouped):
                ws = sorted(grouped[key], key=lambda x: x["x0"])
                left_words = [w for w in ws if w["x0"] < x_cut]
                right_words = [w for w in ws if w["x0"] >= x_cut]

                left = clean_text(" ".join(w["text"] for w in left_words))
                right = clean_text(" ".join(w["text"] for w in right_words))
                full = clean_text(" ".join(w["text"] for w in ws))

                line_rows.append({
                    "page": page_no,
                    "key": key,
                    "left": left,
                    "right": right,
                    "full": full,
                })

    pdf_file.seek(0)

    # Crop to the audit findings body.
    start_idx = 0
    for i, ln in enumerate(line_rows):
        if re.search(r"No\.\s+Audit Findings\s+Recommendation", ln["full"], re.I):
            start_idx = i + 1
            break
        if clean_text(ln["left"]).lower() == "no.":
            start_idx = i + 1
            break

    end_idx = len(line_rows)
    for i, ln in enumerate(line_rows[start_idx:], start_idx):
        if re.search(r"Prepared/Audited by:|Prepared by:|Reviewed by:|Noted by:|^cc:|^EXHIBIT\s+A|^Request for Soft Copy", ln["full"], re.I):
            end_idx = i
            break

    body_lines = line_rows[start_idx:end_idx]

    # Detect issue title entries from the LEFT/Audit Findings column.
    entries = []
    i = 0
    while i < len(body_lines):
        first_title = extract_title_prefix(body_lines[i]["left"])
        if not first_title:
            i += 1
            continue

        start = i
        title_parts = [first_title]
        i += 1

        while i < len(body_lines):
            nxt = extract_title_prefix(body_lines[i]["left"])
            if nxt:
                title_parts.append(nxt)
                i += 1
            else:
                break

        entries.append({
            "start": start,
            "end_title": i,
            "title": normalize_title(" ".join(title_parts)),
        })

    for idx, entry in enumerate(entries):
        next_start = entries[idx + 1]["start"] if idx + 1 < len(entries) else len(body_lines)
        segment = body_lines[entry["start"]:next_start]

        narrative_lines = []
        for ln in body_lines[entry["end_title"]:next_start]:
            left = clean_text(ln["left"])
            if not left:
                continue
            # Remove extracted issue-number artifacts like "1." or "4. consolidate...".
            left = re.sub(r"^\d{1,2}\.\s*", "", left).strip()
            if left:
                narrative_lines.append(left)

        right_lines = []
        right_noise = {"of", "to", "the", "be", "no", "not", "as"}
        for ln in segment:
            rtxt = clean_text(ln["right"])
            if not rtxt:
                continue
            if rtxt.lower() in right_noise:
                continue
            right_lines.append(rtxt)

        issue_title = entry["title"]
        narrative = "\n".join(narrative_lines)
        recommendation_raw = "\n".join(right_lines)
        recommendation = normalize_recommendation(recommendation_raw) if recommendation_raw else "None"

        # If the recommendation column is blank but the left segment has standalone NONE, treat as None.
        if not recommendation_raw and any(clean_text(ln["left"]).upper() in ["NONE", "NONE."] for ln in segment):
            recommendation = "None"

        rows.append({
            "issue_no": str(idx + 1),
            "issue": issue_title,
            "narrative": remove_action_taken(narrative),
            "recommendation1": recommendation,
            "recommendation2": "None",
            "explanation": extract_explanation_from_narrative(narrative),
            "correction": extract_correction_from_text("\n".join([ln["left"] for ln in segment] + [ln["right"] for ln in segment])),
        })

    return rows

def filter_no_findings_when_other_issues(items):
    # Keep every numbered row. A separate No Findings row can be valid for a specific auditee/activity.
    return items


def classify_audit_type(text):
    sales_terms = ["area sales representative", "district sales supervisor", "regional sales supervisor", "technical sales supervisor", "sales personnel"]
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
        reaction = detect_reaction(item["issue"], item["narrative"], item["recommendation1"])
        frequency = detect_frequency(item["issue"], item["narrative"], item["recommendation1"])

        if manual is not None:
            task_id = clean_text(manual.get("Task ID", "")) or task_id
            auditor = clean_text(manual.get("Auditor", "")) or auditor
            reaction = clean_text(manual.get("Reaction", "")) or reaction
            frequency = clean_text(manual.get("Frequency", "")) or frequency

        findings = classify_finding(item["issue"], item["recommendation1"], item["narrative"], header.get("company", ""), header.get("audit_title", ""))
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
            item["issue"],
            item["explanation"] or "None", item["recommendation1"] or "None",
            item["recommendation2"] or "None", auditor or "None", "None",
            reaction, frequency, item["correction"] or "None", "", case_status,
            score, improve, net, "Individual", user,
        ])

    return pd.DataFrame(rows, columns=HEADERS), header, items


def excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Audit Extraction")
        ws = writer.book["Audit Extraction"]
        ws.freeze_panes = "A2"
        for cell in ws[1]:
            cell.font = cell.font.copy(bold=True)
            cell.alignment = cell.alignment.copy(horizontal="center", vertical="center", wrap_text=True)
        widths = {
            "A": 5, "B": 14, "C": 18, "D": 18, "E": 16, "F": 14, "G": 28,
            "H": 12, "I": 16, "J": 10, "K": 55, "L": 60, "M": 60, "N": 60,
            "O": 35, "P": 28, "Q": 14, "R": 24, "S": 18, "T": 32, "U": 12,
            "V": 20, "W": 10, "X": 14, "Y": 12, "Z": 14, "AA": 12,
        }
        for col, width in widths.items():
            ws.column_dimensions[col].width = width
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = cell.alignment.copy(wrap_text=True, vertical="top")
    return output.getvalue()