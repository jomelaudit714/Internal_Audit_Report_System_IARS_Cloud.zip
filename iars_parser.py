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
    "Noel Buena",
    "Jomel Santiago",
    "Sarina Amuraw",
    "Patricia Anne S. Del Rosario",
    "Cris Canonoy",
    "Antonio P. Bides",
    "Jed Laserna",
    "Antonio Trece Generato Jr.",
    "Joshua Christopher Catis",
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


def normalize_for_match(value):
    """Normalize names for robust matching."""
    return re.sub(r"[^A-Z0-9 ]", " ", clean_text(value).upper()).strip()


def load_auditor_records(auditors_df=None):
    """Return auditor records from Master Data Auditors sheet.

    Expected columns: Auditor, User, Status.
    Falls back to hardcoded AUDITORS if sheet is unavailable.
    """
    records = []

    if auditors_df is not None and not getattr(auditors_df, "empty", True):
        for _, r in auditors_df.iterrows():
            auditor = clean_text(r.get("Auditor", ""))
            if not auditor:
                continue

            status = clean_text(r.get("Status", "Active"))
            if status and status.lower() not in ["active", ""]:
                continue

            user = clean_text(r.get("User", ""))
            records.append({
                "auditor": auditor,
                "user": user or auditor.split()[0],
                "norm": normalize_for_match(auditor),
            })

    if not records:
        for auditor in AUDITORS:
            records.append({
                "auditor": auditor,
                "user": auditor.split()[0],
                "norm": normalize_for_match(auditor),
            })

    return records


def prepared_by_auditor(text, auditors_df=None):
    """Detect Prepared/Audited By name from PDF and return canonical Auditor name from Master Data."""
    # Do not stop at Noted by because PDF table extraction can place "Noted by:" beside Prepared by.
    m = re.search(
        r"Prepared(?:/Audited)? by\s*:\s*(.+?)(?:Reviewed by|cc:|Audit/file|$)",
        text,
        re.I | re.S,
    )

    area = m.group(1) if m else text
    area_norm = normalize_for_match(area)

    matches = []
    for rec in load_auditor_records(auditors_df):
        norm_name = rec["norm"]
        tokens = [t for t in norm_name.split() if len(t) > 1]

        positions = []

        # Exact normalized name match.
        pos = area_norm.find(norm_name)
        if pos >= 0:
            positions.append(pos)

        # First + last token match handles middle initials and punctuation.
        if len(tokens) >= 2:
            first, last = tokens[0], tokens[-1]
            pos_first = area_norm.find(first)
            pos_last = area_norm.find(last)
            if pos_first >= 0 and pos_last >= 0 and pos_first <= pos_last:
                positions.append(pos_first)

        # Multi-token partial match: useful for names like Patricia Anne S. Del Rosario.
        hit_count = sum(1 for t in tokens if t in area_norm)
        if tokens and hit_count >= min(len(tokens), 3):
            found_positions = [area_norm.find(t) for t in tokens if area_norm.find(t) >= 0]
            if found_positions:
                positions.append(min(found_positions))

        if positions:
            matches.append((min(positions), -len(norm_name), rec["auditor"]))

    if matches:
        return sorted(matches)[0][2]

    return "None"


def auditor_user(auditor, auditors_df=None):
    """Return User column from Master Data Auditors sheet for the detected auditor."""
    auditor_norm = normalize_for_match(auditor)

    for rec in load_auditor_records(auditors_df):
        if rec["norm"] == auditor_norm:
            return rec["user"]

    # fallback first/last matching
    auditor_tokens = [t for t in auditor_norm.split() if len(t) > 1]
    for rec in load_auditor_records(auditors_df):
        rec_tokens = [t for t in rec["norm"].split() if len(t) > 1]
        if auditor_tokens and rec_tokens and auditor_tokens[0] == rec_tokens[0] and auditor_tokens[-1] == rec_tokens[-1]:
            return rec["user"]

    return auditor.split()[0] if auditor and auditor != "None" else "None"


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

    # Keep only the actual issue title when activity/auditee/company title is mixed with it.
    for key in PRIORITY_TITLES:
        if key in upper:
            return clean_text(title[upper.find(key):])

    # Special case: minimal cash overage should still be treated as cash overage,
    # while preserving the amount in the issue title.
    if "MINIMAL CASH OVERAGE" in upper:
        idx = upper.find("CASH OVERAGE")
        return clean_text(title[idx:]) if idx >= 0 else title

    if upper in ["OTHER ISSUE", "OTHER ISSUES"]:
        return "OTHER ISSUE"

    return title


def infer_issue_title_from_narrative(issue_title, narrative):
    """Convert generic issue titles into meaningful issue titles without changing audit thought."""
    title = clean_text(issue_title)
    text = clean_text(narrative)
    lower = text.lower()

    if title.upper() not in ["OTHER ISSUE", "OTHER ISSUES"]:
        return title

    if "budget" in lower and ("petty cash request" in lower or "pcr" in lower):
        if (
            "does not require" in lower
            or "absence of a pcr" in lower
            or "submitted prior to the release" in lower
            or "submit the pcr only upon liquidation" in lower
        ):
            return "BUDGET RELEASE WITHOUT PRIOR PCR"

    if "without pcr" in lower or "no pcr" in lower:
        return "BUDGET RELEASE WITHOUT PRIOR PCR"

    return title



def enhance_issue_title_details(issue_title, narrative):
    """Add missing-detail qualifier to generic issue titles when the report identifies the field."""
    title = clean_text(issue_title)
    lower_title = title.lower()
    text = clean_text(f"{issue_title} {narrative}")
    lower = text.lower()

    if lower_title.startswith("incomplete details in pcv"):
        m = re.search(r"incomplete details in pcv\s*:\s*(.+)", title, re.I)
        if m:
            details = clean_text(m.group(1)).upper()
            return f"INCOMPLETE DETAILS IN PCV - {details}"

        fields = []
        quoted = re.findall(r"[“\"]([^”\"]+)[”\"]", text)
        for q in quoted:
            q_clean = clean_text(q).strip()
            if q_clean and len(q_clean) <= 50:
                fields.append(q_clean.upper())

        if "recipient" in lower and "signature" in lower:
            fields.append("RECIPIENT'S SIGNATURE")
        if "pcv date" in lower or ("date" in lower and "pcv" in lower):
            fields.append("PCV DATE")
        if "payee" in lower:
            fields.append("PAYEE")
        if "approved by" in lower:
            fields.append("APPROVED BY")
        elif "approval" in lower or "approver" in lower:
            fields.append("APPROVAL")
        if "signature" in lower and not fields:
            fields.append("SIGNATURE")

        if fields:
            clean_fields = []
            for f in fields:
                if f and f not in clean_fields:
                    clean_fields.append(f)
            return f"INCOMPLETE DETAILS IN PCV - {', '.join(clean_fields)}"

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


def _is_activity_header(upper):
    return upper.strip().rstrip(":") in [
        "REVOLVING FUND COUNT",
        "PETTY CASH FUND",
        "PETTY CASH FUND COUNT",
        "CASH ADVANCES COUNT",
        "CASH ADVANCE COUNT",
        "DAILY SALES COUNT",
        "CASH SALES COUNT",
        "COLLECTION COUNT",
        "CHANGE FUND COUNT",
    ]


def _is_generic_other(upper):
    return upper.strip().rstrip(":") in ["OTHER ISSUE", "OTHER ISSUES"]


def _is_activity_header(upper):
    return upper.strip().rstrip(":") in [
        "REVOLVING FUND COUNT",
        "PETTY CASH FUND",
        "PETTY CASH FUND COUNT",
        "CASH ADVANCES COUNT",
        "CASH ADVANCE COUNT",
        "DAILY SALES COUNT",
        "CASH SALES COUNT",
        "COLLECTION COUNT",
        "CHANGE FUND COUNT",
    ]


def _is_generic_other(upper):
    return upper.strip().rstrip(":") in ["OTHER ISSUE", "OTHER ISSUES"]


def split_finding_cell(finding_cell):
    """Split table finding cell into actual issue title and narrative."""
    lines = [
        clean_text(x)
        for x in str(finding_cell or "").replace("\r", "\n").split("\n")
        if clean_text(x)
    ]

    if not lines:
        return "", ""

    title_index = None
    title_parts = []
    narrative_start = 0

    for i, line in enumerate(lines):
        upper = line.upper().strip().rstrip(":")

        if _is_activity_header(upper) or _is_generic_other(upper):
            continue

        is_real_title = (
            any(k in upper for k in PRIORITY_TITLES)
            or any(k in upper for k in TITLE_KEYWORDS)
            or "UNACCOUNTED CASH" in upper
            or "MINIMAL CASH OVERAGE" in upper
            or "MINIMAL CASH SHORTAGE" in upper
            or "SKIPPED AND MISSING PCV" in upper
            or "NO PRE-PRINTED SERIES" in upper
        )

        if is_real_title and upper_ratio(line) >= 0.70 and len(line) <= 230:
            title_index = i
            title_parts = [line.rstrip(":")]
            j = i + 1

            while j < len(lines):
                nxt = lines[j]
                nxt_upper = nxt.upper().strip().rstrip(":")
                if _is_activity_header(nxt_upper) or _is_generic_other(nxt_upper):
                    j += 1
                    continue

                nxt_is_title_cont = (
                    upper_ratio(nxt) >= 0.70
                    and len(nxt) <= 230
                    and (
                        any(k in nxt_upper for k in PRIORITY_TITLES)
                        or any(k in nxt_upper for k in TITLE_KEYWORDS)
                        or "UNACCOUNTED CASH" in nxt_upper
                        or "NO CASH SHORTAGE/OVERAGE" in nxt_upper
                        or "NO CASH SHORTAGE" in nxt_upper
                        or "NO CASH OVERAGE" in nxt_upper
                    )
                )
                if nxt_is_title_cont:
                    title_parts.append(nxt.rstrip(":"))
                    j += 1
                else:
                    break
            narrative_start = j
            break

    if title_index is None:
        # Do not capture OTHER ISSUE. If no real title is found, infer if possible; otherwise skip.
        if lines and _is_generic_other(lines[0].upper().strip().rstrip(":")):
            narrative = "\n".join(lines[1:])
            inferred = infer_issue_title_from_narrative("OTHER ISSUE", narrative)
            if not _is_generic_other(inferred.upper()):
                return enhance_issue_title_details(inferred, narrative), narrative
            return "", ""

        # Fallback only for non-activity and non-other lines.
        for i, line in enumerate(lines):
            upper = line.upper().strip().rstrip(":")
            if not _is_activity_header(upper) and not _is_generic_other(upper):
                title_index = i
                title_parts = [line.rstrip(":")]
                narrative_start = i + 1
                break

    if title_index is None:
        return "", ""

    raw_title = normalize_title(" ".join(title_parts))
    if _is_activity_header(raw_title.upper()) or _is_generic_other(raw_title.upper()):
        return "", ""

    narrative = "\n".join(lines[narrative_start:])
    issue_title = infer_issue_title_from_narrative(raw_title, narrative)
    issue_title = enhance_issue_title_details(issue_title, narrative)

    return issue_title, narrative


def normalize_recommendation(rec):
    rec = clean_text(rec).replace("NONE.", "None").strip()
    if not rec or rec.upper() in ["NONE", "N/A", "NONE."]:
        return "None"

    # Remove generic recommendation openers while preserving actual instruction.
    rec = re.sub(r"^We recommend(?:ed)?(?: that)?\s+", "", rec, flags=re.I)
    rec = re.sub(r"^We advise\s+", "", rec, flags=re.I)
    rec = re.sub(r"^Please review\s+", "Review ", rec, flags=re.I)

    # Remove auditee name but preserve "Should".
    rec = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ.'\-]*(?:\s+[A-Z][A-Za-zñÑ.'\-]*){0,6}\s+should\b",
        "Should",
        rec,
        flags=re.I,
    )

    # Remove auditee name followed by comma.
    rec = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ.'\-]*(?:\s+[A-Z][A-Za-zñÑ.'\-]*){0,6},\s*",
        "",
        rec,
        flags=re.I,
    )

    # Remove auditee with "and the Finance Department maintain".
    rec = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ.'\-]*(?:\s+[A-Z][A-Za-zñÑ.'\-]*){0,6}\s+and\s+the\s+Finance\s+Department\s+maintain\b",
        "Maintain",
        rec,
        flags=re.I,
    )

    # Remove auditee name for direct actions.
    rec = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ.'\-]*(?:\s+[A-Z][A-Za-zñÑ.'\-]*){0,6}\s+(return|use|update|review|ensure|avoid|explain|prepare|stamp|submit|properly|promptly|monitor|provide|reconcile|account|maintain)\b",
        lambda m: m.group(2).capitalize(),
        rec,
        flags=re.I,
    )

    rec = re.sub(r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ.'\-]*(?:\s+[A-Z][A-Za-zñÑ.'\-]*){0,6}\s+to\s+", "", rec, flags=re.I)

    # Generic wording cleanup.
    rec = re.sub(r"^(the\s+)?custodian\s+to\s+", "", rec, flags=re.I)
    rec = re.sub(r"^(the\s+)?custodian\s+should\s+", "Should ", rec, flags=re.I)
    rec = re.sub(r"^management\s+should\s+", "Should ", rec, flags=re.I)
    rec = re.sub(r"^ensuring\s+that\s+", "Ensure that ", rec, flags=re.I)
    rec = re.sub(r"^to\s+", "", rec, flags=re.I)
    rec = re.sub(r"^The use of\s+(.+?)\s+as\b", r"Use \1 as", rec, flags=re.I)
    rec = re.sub(r"^Records be updated\b", "Update records", rec, flags=re.I)

    return make_sentence(rec)


def split_recommendations(rec):
    """Split recommendation cell into Recommendation1 and Recommendation2."""
    rec = clean_text(rec)
    if not rec or rec.upper() in ["NONE", "N/A", "NONE."]:
        return "None", "None"

    parts = re.split(
        r"\s+(?=(?:Also,|Furthermore,|Further,|In addition,|Moreover,|Additionally,|Likewise,|We recommend(?:ed)?|We advise|Please review|(?:Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-z .'\-]+?\s+should)\b)",
        rec,
        flags=re.I,
    )
    parts = [normalize_recommendation(p) for p in parts if clean_text(p)]
    parts = [p for p in parts if p and p != "None"]

    if not parts:
        return "None", "None"

    rec1 = parts[0]
    rec2 = " ".join(parts[1:]) if len(parts) > 1 else "None"
    return rec1, rec2


def extract_recommendation_pair(segment):
    text = clean_text(segment)
    if not text or text.upper() in ["NONE", "NONE.", "N/A"]:
        return "None", "None"

    rec = re.split(r"Action Taken\s*:", text, flags=re.I)[0]
    return split_recommendations(rec)


def extract_recommendation_from_segment(segment):
    rec1, _ = extract_recommendation_pair(segment)
    return rec1


def remove_action_taken(text):
    return re.split(r"Action Taken\s*:", text or "", flags=re.I)[0]


def _safe_sentence_split(text):
    """Split sentences without breaking common titles like Ms./Mr./Mrs."""
    text = clean_text(text)
    protected = (
        text.replace("Ms.", "Ms<prd>")
            .replace("Mr.", "Mr<prd>")
            .replace("Mrs.", "Mrs<prd>")
            .replace("Dr.", "Dr<prd>")
            .replace("Jr.", "Jr<prd>")
    )
    parts = re.split(r"(?<=[.!?])\s+", protected)
    parts = [p.replace("<prd>", ".") for p in parts]
    return [clean_text(p) for p in parts if clean_text(p)]


def extract_correction_from_text(text):
    m = re.search(r"Action Taken\s*:\s*(.+)", text or "", re.I | re.S)
    if not m:
        return "None"

    val = m.group(1)
    # Stop at next real issue title or recommendation/report footer.
    stop_patterns = [
        r"\bNO PRE-PRINTED SERIES\b",
        r"\bPrepared(?:/Audited)? by:",
        r"\bReviewed by:",
        r"\bNoted by:",
        r"\bcc:",
        r"\bWe recommend\b",
        r"\bWe advise\b",
        r"\bPlease review\b",
    ]

    cut = len(val)
    for pat in stop_patterns:
        mm = re.search(pat, val, re.I | re.M)
        if mm:
            cut = min(cut, mm.start())

    val = clean_text(val[:cut])
    if not val or val.upper() in ["NONE", "N/A", "NO ACTION TAKEN"]:
        return "None"

    # Convert Angelica-style long action taken into concise correction.
    low = val.lower()
    if "gerrie mia montejo" in low and "nikka navarro" in low and "request reimbursement" in low:
        return "The replenishment belonged to the previous custodian and a reimbursement request will be prepared to restore the revolving fund."

    sentences = _safe_sentence_split(val)
    valid = []
    for s in sentences:
        if re.search(r"\b(Ms|Mr|Mrs)\.$", s, re.I):
            continue
        valid.append(s)

    if not valid:
        return "None"

    return make_sentence(" ".join(valid[:2]))


def make_sentence(text):
    text = clean_text(text)
    if not text or text.upper() in ["NONE", "N/A", "NONE."]:
        return "None"
    text = text.strip(" ;,")
    if not text:
        return "None"
    text = text[0].upper() + text[1:]
    if text[-1] not in ".!?":
        text += "."
    return text


def _safe_sentence_split(text):
    """Split sentences without breaking common title abbreviations."""
    text = clean_text(text)
    if not text:
        return []
    protected = (
        text.replace("Ms.", "Ms<prd>")
            .replace("Mr.", "Mr<prd>")
            .replace("Mrs.", "Mrs<prd>")
            .replace("Dr.", "Dr<prd>")
            .replace("Jr.", "Jr<prd>")
            .replace("Art.", "Art<prd>")
    )
    parts = re.split(r"(?<=[.!?])\s+", protected)
    parts = [p.replace("<prd>", ".") for p in parts]
    return [clean_text(p) for p in parts if clean_text(p)]


def _remove_leading_name_fragments(text):
    """Remove incomplete surname/name fragments caused by PDF extraction."""
    text = clean_text(text)
    # "Rtin, she..." / "Fortin, she..." / "Mesa, she..."
    text = re.sub(r"^[A-Z][A-Za-zñÑ.'\-]{1,30},\s+(she|he|they)\b", r"\1", text, flags=re.I)
    text = re.sub(r"^[A-Z][A-Za-zñÑ.'\-]{1,30}\s+(she|he|they)\b", r"\1", text, flags=re.I)
    return clean_text(text)


def _strip_explanation_tail(text):
    text = clean_text(text)
    # Cut obvious non-explanation portions.
    stop_patterns = [
        r"\(See(?: also)? Exhibit [A-Z](?:\.\d+)?\)",
        r"\bWe recommend\b",
        r"\bWe advise\b",
        r"\bPlease review\b",
        r"\bAction Taken\s*:",
        r"\bNONE\.?$",
    ]
    cut = len(text)
    for pat in stop_patterns:
        m = re.search(pat, text, re.I)
        if m:
            cut = min(cut, m.start())
    return _remove_leading_name_fragments(text[:cut])


def _trim_to_explanation_sentence(text, max_words=50):
    text = _strip_explanation_tail(text)
    if not text:
        return "None"

    # If extracted explanation still has a second "She further explained/stated..." clause,
    # keep it only when the full result is short enough; otherwise use the first complete sentence.
    words = text.split()
    if len(words) <= max_words:
        return make_sentence(text)

    sentences = _safe_sentence_split(text)
    if sentences:
        return make_sentence(sentences[0])

    return make_sentence(" ".join(words[:max_words]).rstrip(",;") + "...")


def extract_explanation_from_narrative(narrative):
    """Capture only auditee explanation based on hierarchy.

    Captures the words AFTER:
    1. According to / As per <auditee>,
    2. <auditee> explained/stated/claimed/admitted that
    3. She/He/They further explained/stated/claimed/admitted that

    Names and incomplete surname fragments are removed.
    If no auditee explanation exists, returns None.
    """
    text = clean_text(remove_action_taken(narrative))
    if not text:
        return "None"

    # Do not let recommendation/action text enter explanation.
    text = re.split(r"\b(?:We recommend|We advise|Please review|Action Taken\s*:)", text, flags=re.I)[0]
    text = clean_text(text)

    patterns = [
        # According to Ms. Montejo, she was uncertain...
        r"(?:According to|As per)\s+(?:Mr\.|Ms\.|Mrs\.)?\s*[A-Z][A-Za-zñÑ .'\-]+?,\s*(.+)",
        # Ms. Mesa explained that she was...
        r"(?:Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ .'\-]+?\s+(?:claimed|explained|stated|admitted)\s+(?:that\s+)?(.+)",
        # She further explained that...
        r"\b(?:He|She|They)\s+(?:further\s+)?(?:claimed|explained|stated|admitted)\s+(?:that\s+)?(.+)",
    ]

    for pat in patterns:
        m = re.search(pat, text, re.I | re.S)
        if m:
            return _trim_to_explanation_sentence(m.group(1), 50)

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

    # Explicit no-finding titles/phrases.
    if any(p in combined for p in NO_FINDING_PATTERNS):
        return "No Findings 10"

    amounts = extract_money_amounts(issue) or extract_money_amounts(narrative)
    amount = max(amounts) if amounts else None

    is_estancia = "estancia de lorenzo" in company_lower
    is_petty_cash = "petty cash" in combined or "petty cash" in audit_title_lower
    is_cash_advance = is_cash_advance_context(issue, narrative, audit_title)

    # Special rule: Cash Advance Overage is always No Findings.
    if is_cash_advance and any(k in issue_lower for k in ["cash overage", "fund overage", "collection overage", "overage"]):
        return "No Findings 10"

    # Cash/Fund/Sales/Collection/Daily Sales/Change Fund shortages and overages:
    # evaluate immateriality first before actual finding category.
    is_shortage = any(k in issue_lower for k in ["cash shortage", "fund shortage", "collection shortage", "sales shortage", "change fund shortage", "unaccounted cash", "shortage"])
    is_overage = any(k in issue_lower for k in ["cash overage", "fund overage", "collection overage", "sales overage", "change fund overage", "minimal cash overage", "overage"])

    if (is_shortage or is_overage) and is_immaterial_cash_variance(amount, issue, narrative, audit_title):
        return "Immaterial Findings 3"

    if is_shortage:
        if amount is not None and amount < 3000:
            return "Cash/Fund/Collection Shortage (below ₱3,000.00) -4"
        return "Cash/Fund/Collection Shortage (₱3,000.00 and above) -8"

    if is_overage:
        if amount is not None and amount < 1000:
            return "Cash/Fund/Collection Overage (below ₱1,000.00) -2"
        return "Cash/Fund/Collection Overage (₱1,000.00 and above) -4"

    # Incomplete details in PCV/receipt/generic receipt are completeness lapses,
    # not omission/alteration or nonconformity, unless actual alteration/tampering is stated.
    incomplete_detail_patterns = [
        "incomplete details in pcv",
        "incomplete pcv",
        "incomplete details in petty cash voucher",
        "incomplete receipt information",
        "incomplete generic receipt",
        "incomplete generic receipt information",
        "incomplete official receipt",
        "incomplete sales invoice information",
        "incomplete receipt",
        "incomplete details in transmittal",
    ]
    alteration_patterns = [
        "altered", "alteration", "tampered", "falsified", "erasure",
        "changed amount", "changed date", "unauthorized correction",
        "forged", "fabricated",
    ]
    if any(k in issue_lower for k in incomplete_detail_patterns):
        if any(k in combined for k in alteration_patterns):
            return "Omission & Alteration Of Details in Documents -7"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    # Petty Cash specific hard trigger agreed by audit team.
    if "without stamped" in combined and "paid" in combined:
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    # Company/activity overrides must be specific and should not over-capture generic PCR issues.
    if is_estancia and any(k in combined for k in ["policy", "procedure", "proper procedure", "guidelines", "sop", "cash voucher"]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    if is_petty_cash and any(k in combined for k in ["reimbursement exceeding", "without stamped paid", "unsupported receipt", "unsupported invoice", "official receipt without", "invoice without"]):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    if any(k in issue_lower for k in ["incorrect receipt", "incorrect pcv", "omission", "alteration"]):
        if any(k in combined for k in ["altered", "alteration", "tampered", "falsified", "erasure", "forged", "fabricated"]):
            return "Omission & Alteration Of Details in Documents -7"
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "required by policy"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["late preparation of pcv", "no preparation of pcv", "uncancelled pcv", "inconsistent using of pcv"]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "required by policy"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if "skipped and missing pcv" in issue_lower or ("missing pcv" in issue_lower and "skipped" in issue_lower):
        return "Missing, Misused or Lost Of Documents/Asset(s) -3"

    if any(k in issue_lower for k in ["no document used for cash taken from the fund", "cash taken without document", "no document used"]):
        if any(k in combined for k in ["lost document", "missing document", "cannot produce", "unable to locate", "misused document"]):
            return "Missing, Misused or Lost Of Documents/Asset(s) -3"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["undocumented", "without document"]):
        if any(k in combined for k in ["lost document", "missing document", "cannot produce", "unable to locate", "misused document"]):
            return "Missing, Misused or Lost Of Documents/Asset(s) -3"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["inaccurate monitoring", "outdated monitoring", "no daily balancing", "no monitoring", "incomplete monitoring", "delayed recording"]):
        if any(k in combined for k in ["policy", "procedure", "sop", "guideline", "proper procedure"]):
            return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["depleted fund", "low fund", "fund depletion", "mixing of fund", "mixed fund", "personal cash", "outside its purpose", "budget release without prior pcr"]):
        return "Ignore or Disregard Office/Operation Best Practices -3"

    # Nonconformity trigger: only when the recommendation/narrative explicitly refers to process/policy/procedure/guideline/SOP/memorandum.
    nonconf_patterns = [
        "nonconformity", "non-conformity", "non-compliance",
        "not following proper procedure", "policy", "policies", "procedure", "procedures",
        "guideline", "guidelines", "sop", "memorandum", "written requirement",
        "please review process", "please review guidelines", "please review procedure", "please review policy",
        "review process", "review guidelines", "review procedure", "review policy",
    ]
    if any(k in combined for k in nonconf_patterns):
        return "Nonconformity With The Written Policies, Guidelines, Process And Procedures -4"

    if "uncooperative" in combined:
        return "Uncooperative or Failed To Produce Documents/Results Within Reasonable Time -4"
    if "immaterial" in combined:
        return "Immaterial Findings 3"

    return "Ignore or Disregard Office/Operation Best Practices -3"


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

    if "skipped and missing pcv" in issue_lower or ("missing pcv" in issue_lower and "skipped" in issue_lower):
        return "Missing, Misused or Lost Of Documents/Asset(s) -3"

    if any(k in issue_lower for k in ["no document used for cash taken from the fund", "cash taken without document", "no document used"]):
        if any(k in combined for k in ["lost document", "missing document", "cannot produce", "unable to locate", "misused document"]):
            return "Missing, Misused or Lost Of Documents/Asset(s) -3"
        return "Ignore or Disregard Office/Operation Best Practices -3"

    if any(k in issue_lower for k in ["undocumented", "without document"]):
        if any(k in combined for k in ["lost document", "missing document", "cannot produce", "unable to locate", "misused document"]):
            return "Missing, Misused or Lost Of Documents/Asset(s) -3"
        return "Ignore or Disregard Office/Operation Best Practices -3"

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
    text = clean_text(segment)
    if not text or text.upper() in ["NONE", "NONE.", "N/A"]:
        return "None"

    # In table-based PDFs, the recommendation cell is already separated.
    # Capture direct "should" recommendation styles, "Also" paragraphs, and normal recommendation phrases.
    rec = re.split(r"Action Taken\s*:", text, flags=re.I)[0]
    rec1, rec2 = split_recommendations(rec)

    # Store rec2 temporarily in a module-level variable only for row builder fallback if needed.
    # Main extraction uses extract_recommendation_pair below.
    return rec1


def extract_recommendation_pair(segment):
    text = clean_text(segment)
    if not text or text.upper() in ["NONE", "NONE.", "N/A"]:
        return "None", "None"

    rec = re.split(r"Action Taken\s*:", text, flags=re.I)[0]
    return split_recommendations(rec)


def concise_text(text, max_words=25, field="general"):
    """Make extracted text concise and understandable without changing the audit thought."""
    text = clean_text(text)
    if not text or text.upper() in ["NONE", "N/A", "NONE."]:
        return "None"

    if field == "correction" and re.search(r"\b(Ms|Mr|Mrs)\.?$", text, re.I):
        return "None"

    text = re.sub(r"\(See(?: also)? Exhibit [A-Z](?:\.\d+)?\)", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()

    text = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-z .]+?\s+(explained|stated|claimed|admitted)\s+that\s+",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(r"^(According to|As per)\s+(Mr\.|Ms\.|Mrs\.)?\s*[A-Z][A-Za-z .]+?,?\s*", "", text, flags=re.I)
    text = re.sub(r"^(It was observed that|It was noted that|The audit noted that)\s+", "", text, flags=re.I)

    if field.startswith("recommendation"):
        text = normalize_recommendation(text)

    words = text.split()
    if len(words) <= max_words:
        return make_sentence(text)

    if field == "correction":
        # Do not split at Ms./Mr./Mrs. abbreviations.
        sentences = _safe_sentence_split(text) if "_safe_sentence_split" in globals() else []
        if sentences and len(sentences[0].split()) <= max_words:
            return make_sentence(sentences[0].strip())
        return make_sentence(" ".join(words[:max_words]).rstrip(",;") + "...")

    sentences = re.split(r"(?<=[.!?])\s+", text)
    if sentences and len(sentences[0].split()) <= max_words:
        return make_sentence(sentences[0].strip())

    return make_sentence(" ".join(words[:max_words]).rstrip(",;") + "...")


def extract_accountability_amount(text):
    """Extract base/accountability amount for variance percentage computation."""
    patterns = [
        r"total accountability of\s*(?:₱|P)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2})?)",
        r"accountability of\s*(?:₱|P)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2})?)",
        r"accountability amount(?:ing)? to\s*(?:₱|P)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2})?)",
        r"total cash available was\s*(?:₱|P)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})|[0-9]+(?:\.[0-9]{1,2})?)",
    ]

    for pat in patterns:
        m = re.search(pat, text or "", re.I)
        if m:
            try:
                return float(m.group(1).replace(",", ""))
            except Exception:
                pass
    return None


def is_cash_advance_context(issue, narrative, audit_title=""):
    text = clean_text(f"{issue} {narrative} {audit_title}").lower()
    return "cash advance" in text or "cash advances" in text


def is_cash_accountability_context(issue, narrative, audit_title=""):
    text = clean_text(f"{issue} {narrative} {audit_title}").lower()
    terms = [
        "petty cash", "revolving fund", "cash advance", "cash advances", "cash sales",
        "sales collection", "daily sales", "change fund", "collection", "fund"
    ]
    return any(t in text for t in terms)


def is_immaterial_cash_variance(amount, issue, narrative, audit_title=""):
    """Immaterial if P0.01-P99.00 or variance percent <= 0.05%."""
    if amount is None or amount <= 0:
        return False

    if not is_cash_accountability_context(issue, narrative, audit_title):
        return False

    if 0.01 <= amount <= 99.00:
        return True

    base = extract_accountability_amount(narrative)
    if base and base > 0:
        variance_pct = (amount / base) * 100
        if variance_pct <= 0.05:
            return True

    return False


def is_no_or_immaterial_finding(finding_text, issue_text=""):
    combined = clean_text(f"{finding_text} {issue_text}").lower()
    return (
        "immaterial findings" in combined
        or "no findings" in combined
        or "no cash shortage" in combined
        or "no cash overage" in combined
        or "no cash shortage/overage" in combined
        or "no cash overage/shortage" in combined
        or "no shortage/overage" in combined
        or "no overage/shortage" in combined
        or "fund is intact" in combined
    )


def filter_rows_by_task_id(row_dicts):
    """Remove no-finding/immaterial rows only when same Task ID has actual findings.

    If Task ID is blank/None, all rows are treated as one task.
    If different Task IDs are supplied, each Task ID is evaluated separately.
    """
    grouped = {}
    for row in row_dicts:
        task_id = clean_text(row.get("task_id", "")) or "None"
        grouped.setdefault(task_id, []).append(row)

    final_rows = []
    for task_id, rows in grouped.items():
        actual = [
            r for r in rows
            if not is_no_or_immaterial_finding(r.get("findings", ""), r.get("issue", ""))
        ]
        if actual:
            final_rows.extend(actual)
        else:
            final_rows.extend(rows)

    return final_rows
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
    """Extract finding rows from PDF.

    Primary method uses table extraction so Audit Findings and Recommendation stay separated.
    Fallback method uses title-line extraction for irregular PDFs.
    """
    rows = []
    pdf_file.seek(0)

    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                for row in table:
                    if not row:
                        continue

                    cells = [clean_cell_preserve(c) for c in row]
                    issue_no = None
                    for c in cells:
                        m = re.fullmatch(r"\s*(\d{1,2})\.?\s*", clean_text(c))
                        if m:
                            issue_no = m.group(1)
                            break

                    if not issue_no:
                        continue

                    non_empty = [c for c in cells if clean_text(c)]
                    if len(non_empty) < 2:
                        continue

                    if clean_text(non_empty[0]).rstrip(".") != issue_no:
                        continue

                    finding_cell = non_empty[1] if len(non_empty) >= 2 else ""
                    rec_cell = non_empty[2] if len(non_empty) >= 3 else "None"

                    if not clean_text(finding_cell):
                        continue

                    issue_title, narrative = split_finding_cell(finding_cell)
                    recommendation, recommendation2 = extract_recommendation_pair(rec_cell)

                    if not clean_text(issue_title):
                        continue

                    rows.append({
                        "issue_no": issue_no,
                        "issue": issue_title,
                        "narrative": remove_action_taken(narrative),
                        "recommendation1": recommendation,
                        "recommendation2": recommendation2,
                        "explanation": extract_explanation_from_narrative(narrative),
                        "correction": extract_correction_from_text(narrative + "\n" + clean_text(rec_cell)),
                    })

    pdf_file.seek(0)
    if rows:
        return rows

    # Fallback for irregular PDFs.
    text = extract_all_text(pdf_file)
    body = crop_report_body(text)
    lines = [x.rstrip() for x in body.split("\n") if clean_text(x)]
    entries = find_issue_title_entries(lines)
    fallback_rows = []

    for idx, entry in enumerate(entries):
        next_start = entries[idx + 1]["start"] if idx + 1 < len(entries) else len(lines)
        segment_lines = lines[entry["start"]:next_start]
        segment = "\n".join(segment_lines)
        narrative_segment = "\n".join(lines[entry["end_title"]:next_start])
        issue_title = infer_issue_title_from_narrative(entry["title"], narrative_segment)

        rec1, rec2 = extract_recommendation_pair(segment)
        fallback_rows.append({
            "issue_no": str(idx + 1),
            "issue": issue_title,
            "narrative": remove_action_taken(narrative_segment),
            "recommendation1": rec1,
            "recommendation2": rec2,
            "explanation": extract_explanation_from_narrative(narrative_segment),
            "correction": extract_correction_from_text(segment),
        })

    return fallback_rows


    for idx, entry in enumerate(entries):
        start = entry["start"]
        next_start = entries[idx + 1]["start"] if idx + 1 < len(entries) else len(lines)
        segment_lines = lines[start:next_start]
        segment = "\n".join(segment_lines)
        issue_title = entry["title"]
        narrative_segment = "\n".join(lines[entry["end_title"]:next_start])

        rows.append({
            "issue_no": str(idx + 1),
            "issue": issue_title,
            "narrative": remove_action_taken(narrative_segment),
            "recommendation1": extract_recommendation_from_segment(segment),
            "recommendation2": "None",
            "explanation": extract_explanation_from_narrative(narrative_segment),
            "correction": extract_correction_from_text(segment),
        })

    return rows


def filter_no_findings_when_other_issues(items):
    # Row filtering is now handled after classification using Task ID in build_records().
    return items



def classify_audit_type(text):
    sales_terms = ["area sales representative", "district sales supervisor", "regional sales supervisor", "technical sales supervisor", "sales personnel"]
    return "Operations Audit" if any(t in text.lower() for t in sales_terms) else "Financial Audit"


def build_records(pdf_file, master_df=None, manual_df=None, auditors_df=None):
    text = extract_all_text(pdf_file)
    header = extract_header(text)
    emp_id, emp_name = match_employee(master_df, header["auditee_name"])
    auditor_default = prepared_by_auditor(text, auditors_df)
    audit_type = classify_audit_type(text)
    items = extract_finding_rows_from_pdf(pdf_file)

    manual_map = {}
    if manual_df is not None and not manual_df.empty:
        for _, r in manual_df.iterrows():
            issue_no = clean_text(r.get("Issue No.", ""))
            if issue_no:
                manual_map[issue_no] = r

    row_dicts = []

    for row_no, item in enumerate(items, 1):
        manual = manual_map.get(item["issue_no"])
        task_id = header["task_id"]
        auditor = auditor_default

        issue_title = infer_issue_title_from_narrative(item["issue"], item["narrative"])
        issue_title = enhance_issue_title_details(issue_title, item["narrative"])
        item["issue"] = issue_title

        recommendation1 = concise_text(item.get("recommendation1", "None"), 24, "recommendation1")
        recommendation2 = concise_text(item.get("recommendation2", "None"), 24, "recommendation2")
        explanation = make_sentence(item.get("explanation", "None"))
        correction = concise_text(item.get("correction", "None"), 24, "correction")

        reaction = detect_reaction(issue_title, item["narrative"], recommendation1)
        frequency = detect_frequency(issue_title, item["narrative"], recommendation1)

        if manual is not None:
            task_id = clean_text(manual.get("Task ID", "")) or task_id
            auditor = clean_text(manual.get("Auditor", "")) or auditor
            reaction = clean_text(manual.get("Reaction", "")) or reaction
            frequency = clean_text(manual.get("Frequency", "")) or frequency

        findings = classify_finding(
            issue_title,
            recommendation1,
            item["narrative"],
            header.get("company", ""),
            header.get("audit_title", ""),
        )

        score = parse_score(findings)

        if "No Findings" in findings or "Immaterial Findings" in findings:
            reaction = "Maintaining Status Quo"
            frequency = "Not Applicable"

        improve = RESPONSE_RATE.get(reaction, 0) * FREQUENCY_RATE.get(frequency, 1)
        net = score + improve
        case_status = "No Case/Issue" if ("No Findings" in findings or "Immaterial Findings" in findings) else "Follow-up with HR"
        user = auditor_user(auditor, auditors_df)

        row_dicts.append({
            "row_no": row_no,
            "task_id": task_id or "None",
            "issue": issue_title,
            "findings": findings,
            "row": [
                row_no, date.today().isoformat(), audit_type, header["date_reported"],
                header["audit_reference"], emp_id, emp_name, task_id or "None",
                header["scope_date"], header["year"], findings,
                issue_title,  # Issue Detail Issue = exact issue title.
                explanation or "None", recommendation1 or "None",
                recommendation2 or "None", auditor or "None", "None",
                reaction, frequency, correction or "None", "", case_status,
                score, improve, net, "Individual", user,
            ],
        })

    # Task ID based filter:
    # - Blank/None Task ID means all findings in the report are same task.
    # - Different Task IDs are evaluated separately.
    # - If actual findings exist in a task, No Findings/Immaterial rows are removed for that task.
    filtered = filter_rows_by_task_id(row_dicts)

    rows = []
    for new_no, row_info in enumerate(filtered, 1):
        row = row_info["row"]
        row[0] = new_no
        rows.append(row)

    return pd.DataFrame(rows, columns=HEADERS), header, items


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
        user = auditor_user(auditor, auditors_df)

        rows.append([
            row_no, date.today().isoformat(), audit_type, header["date_reported"],
            header["audit_reference"], emp_id, emp_name, task_id or "None",
            header["scope_date"], header["year"], findings,
            make_issue_summary(item["issue"], item["narrative"]),
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