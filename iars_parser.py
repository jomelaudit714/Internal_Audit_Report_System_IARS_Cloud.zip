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



def split_finding_cell(finding_text):
    """Split Audit Findings cell into issue title and narrative.

    Uses the bold/uppercase issue title first, then falls back to known title keywords.
    Audit activity/auditee name before a real issue title is ignored through normalize_title().
    """
    raw = (finding_text or "").replace("\r", "\n")
    clean_raw = clean_text(raw)
    if not clean_raw:
        return "", ""

    upper = clean_raw.upper()

    # Locate actual issue title using priority titles.
    title_start = 0
    matched_key = None
    for key in PRIORITY_TITLES:
        pos = upper.find(key)
        if pos >= 0:
            title_start = pos
            matched_key = key
            break

    if matched_key:
        fragment = clean_raw[title_start:].strip()
        key_len = len(matched_key)

        # Include amount/percentage immediately after the title, if present.
        tail = fragment[key_len:]
        amount_tail = re.match(
            r"\s*[:–-]\s*\(?\s*(?:₱|P)?\s*[0-9][0-9,]*(?:\.[0-9]+)?%?\s*\)?",
            tail,
            flags=re.I,
        )

        title_end = key_len + (amount_tail.end() if amount_tail else 0)
        title = fragment[:title_end].strip(" :")
        narrative = fragment[title_end:].strip()
        return clean_text(normalize_title(title)), clean_text(narrative)

    # No priority title found: use narrative starters to separate title and body.
    working = clean_raw
    narrative_starts = [
        "Surprise", "During", "Upon", "There ", "Details",
        "According", "As per", "Ms.", "Mr.", "We requested",
        "At the commencement", "On June", "All cash",
    ]

    end_candidates = []
    for starter in narrative_starts:
        m = re.search(r"\b" + re.escape(starter) + r"\b", working, flags=re.I)
        if m and m.start() > 0:
            end_candidates.append(m.start())

    if end_candidates:
        title = working[:min(end_candidates)].strip(" :")
        narrative = working[min(end_candidates):].strip()
    else:
        lines = [clean_text(x) for x in raw.split("\n") if clean_text(x)]
        title_lines = []
        body_lines = []
        mode = "title"
        for line in lines:
            low = line.lower()
            if mode == "title":
                if (
                    (upper_ratio(line) >= 0.85 or any(k in line.upper() for k in TITLE_KEYWORDS))
                    and not low.startswith(("surprise", "during", "upon", "there ", "according", "as per", "ms.", "mr."))
                    and len(line) <= 180
                ):
                    title_lines.append(line.strip(" :"))
                    continue
                mode = "body"
            body_lines.append(line)
        title = " ".join(title_lines) if title_lines else lines[0]
        narrative = " ".join(body_lines) if body_lines else clean_raw.replace(title, "", 1).strip()

    return clean_text(normalize_title(title)), clean_text(narrative)

def normalize_recommendation(rec):
    rec = clean_text(rec).replace("NONE.", "None").strip()
    if not rec or rec.upper() in ["NONE", "N/A", "NONE."]:
        return "None"

    rec = re.sub(r"^We recommend(?: that)?\s+", "", rec, flags=re.I)
    rec = re.sub(r"^We advise\s+", "", rec, flags=re.I)
    rec = re.sub(r"^Please review\s+", "Review ", rec, flags=re.I)

    # Remove named subject while preserving requested action.
    action_verbs = r"properly document|return|use|update|review|ensure|avoid|explain|prepare|submit|document|cancel|monitor|reconcile|promptly prepare"
    if re.match(r"^(Mr\.|Ms\.|Mrs\.)\s+", rec, flags=re.I):
        m = re.search(rf"\b(?:should\s+|to\s+)?({action_verbs})\b", rec, flags=re.I)
        if m:
            rec = rec[m.start(1):]

    rec = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ .'-]+?\s+(?:should\s+|to\s+)",
        "",
        rec,
        flags=re.I,
    )
    rec = re.sub(r"^(The custodian|The employee|The auditee|Management|The responsible personnel)\s+(?:should\s+|to\s+)?", "", rec, flags=re.I)

    rec = re.sub(r"^The use of\s+(.+?)\s+as\b", r"Use \1 as", rec, flags=re.I)
    rec = re.sub(r"^Records be updated\b", "Update records", rec, flags=re.I)

    rec = clean_text(rec)
    return rec[0].upper() + rec[1:] if rec else "None"

def remove_person_lead(text):
    """Remove leading names/honorifics while preserving the audit thought."""
    text = clean_text(text)

    # Direct explanations: "Ms. X explained/stated/claimed that ..."
    text = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ .'-]+?\s+(claimed|explained|stated|admitted)\s+that\s+",
        "",
        text,
        flags=re.I,
    )
    text = re.sub(
        r"^(Mr\.|Ms\.|Mrs\.)\s+[A-Z][A-Za-zñÑ .'-]+?\s+(claimed|explained|stated|admitted)\s+",
        "",
        text,
        flags=re.I,
    )

    # "According to/As per Ms. X, she..." or "As per Ms. X she..."
    m = re.match(
        r"^(According to|As per)\s+(?:(Mr\.|Ms\.|Mrs\.)\s+)?[A-Z][A-Za-zñÑ .'-]+?(?:,\s*|\s+)(he|she|they|the)\b\s*(.*)$",
        text,
        flags=re.I,
    )
    if m:
        pronoun = m.group(3)
        rest = m.group(4)
        text = clean_text(f"{pronoun} {rest}")

    text = re.sub(r"^The audit noted that\s+", "", text, flags=re.I)
    text = re.sub(r"^It was noted that\s+", "", text, flags=re.I)
    text = re.sub(r"^Management explained that\s+", "", text, flags=re.I)
    return clean_text(text)

def trim_to_sentence(text, max_words=25):
    """Keep complete sentence when possible; otherwise trim by words."""
    text = clean_text(text)
    if not text or text == "None":
        return "None"

    # Remove exhibit references and extra report marks.
    text = re.sub(r"\(See Exhibit [A-Z](?:\.\d+)?\)", "", text, flags=re.I)
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()
    if len(words) <= max_words:
        return text

    # Prefer a complete first sentence if it is not too long.
    sentences = re.split(r"(?<=[.!?])\s+", text)
    if sentences:
        first = clean_text(sentences[0])
        if 5 <= len(first.split()) <= max_words:
            return first

    return " ".join(words[:max_words]).rstrip(",;:") + "..."


def concise_text(text, field="general", max_words=25):
    """Make explanation/recommendation/correction concise without changing the intent."""
    text = clean_text(text)
    if not text or text == "None":
        return "None"

    text = remove_person_lead(text)

    # Common explanation cleanup from cash count reports.
    text = re.sub(r"^this was her personal cash and that she overlooked the receipt", "Personal cash was overlooked and mixed with the fund", text, flags=re.I)
    text = re.sub(r"^this was his personal cash and that he overlooked the receipt", "Personal cash was overlooked and mixed with the fund", text, flags=re.I)
    text = re.sub(r"^she stated that she forgot to prepare", "The custodian forgot to prepare", text, flags=re.I)
    text = re.sub(r"^he stated that he forgot to prepare", "The custodian forgot to prepare", text, flags=re.I)
    if text:
        text = text[0].upper() + text[1:]

    if field == "recommendation":
        # Convert recommendation to direct action while preserving meaning.
        text = re.sub(r"^(The custodian|The employee|The auditee|Management|The responsible personnel)\s+(?:should\s+|to\s+)?", "", text, flags=re.I)
        text = re.sub(r"^should\s+", "", text, flags=re.I)
        text = re.sub(r"^to\s+", "", text, flags=re.I)
        return trim_to_sentence(text, max_words=max_words)

    if field == "correction":
        if re.search(r"presented a copy of the request.*consolidation", text, flags=re.I):
            return "Request for fund consolidation was presented for approval."
        return trim_to_sentence(text, max_words=max_words)

    if field == "explanation":
        return trim_to_sentence(text, max_words=max_words)

    return trim_to_sentence(text, max_words=max_words)


def split_recommendation_fields(recommendation):
    """Split recommendation into primary action and secondary/preventive action when present."""
    recommendation = clean_text(recommendation)
    if not recommendation or recommendation == "None":
        return "None", "None"

    # Strong split markers used in actual audit reports.
    markers = [
        r"\bAlso,\s+",
        r"\bIn addition,\s+",
        r"\bFurther,\s+",
        r"\bFurthermore,\s+",
        r"\bMoreover,\s+",
    ]

    for marker in markers:
        m = re.search(marker, recommendation, flags=re.I)
        if m:
            first = recommendation[:m.start()].strip(" .;")
            second = recommendation[m.end():].strip(" .;")
            return (
                concise_text(first, "recommendation", 24),
                concise_text(second, "recommendation", 24),
            )

    # If multiple sentences and the second is an action/preventive recommendation, split it.
    sentences = [clean_text(s) for s in re.split(r"(?<=[.!?])\s+", recommendation) if clean_text(s)]
    if len(sentences) >= 2:
        second_lower = sentences[1].lower()
        if any(k in second_lower for k in ["ensure", "review", "monitor", "reconcile", "update", "avoid", "maintain", "submit"]):
            return (
                concise_text(sentences[0], "recommendation", 24),
                concise_text(" ".join(sentences[1:]), "recommendation", 24),
            )

    return concise_text(recommendation, "recommendation", 28), "None"


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
        # Evaluate immateriality first before assigning actual overage category.
        if amount is not None and amount < 1000:
            return "Immaterial Findings 3"
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
    """Extract finding rows using PDF tables first, with text fallback.

    This preserves the stable behavior:
    - Issue Detail Issue = exact issue title/bold header
    - Recommendation = recommendation column/text only
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
                    if not any(clean_text(c) for c in cells):
                        continue

                    # Find numbered audit issue row.
                    issue_no = None
                    issue_idx = None
                    for i, c in enumerate(cells):
                        if re.fullmatch(r"\d{1,2}\.?", clean_text(c)):
                            issue_no = clean_text(c).rstrip(".")
                            issue_idx = i
                            break

                    if issue_no is None:
                        continue

                    # Table layouts seen:
                    # 5 columns: issue no, blank, blank, audit findings, recommendation
                    # 3 columns: issue no, audit findings, recommendation
                    non_empty_after = [c for c in cells[issue_idx + 1:] if clean_text(c)]

                    finding_cell = ""
                    rec_cell = ""

                    if len(cells) >= 5 and clean_text(cells[-2]):
                        finding_cell = cells[-2]
                        rec_cell = cells[-1] if clean_text(cells[-1]) else ""
                    elif len(cells) >= 3 and clean_text(cells[-2]):
                        finding_cell = cells[-2]
                        rec_cell = cells[-1] if clean_text(cells[-1]) else ""
                    elif len(non_empty_after) >= 2:
                        finding_cell = non_empty_after[-2]
                        rec_cell = non_empty_after[-1]
                    elif len(non_empty_after) == 1:
                        finding_cell = non_empty_after[0]
                        rec_cell = ""

                    if not clean_text(finding_cell):
                        continue
                    if "Audit Findings" in finding_cell and "Recommendation" in finding_cell:
                        continue

                    issue_title, narrative = split_finding_cell(finding_cell)
                    if not clean_text(issue_title):
                        continue

                    segment = f"{finding_cell}\n{rec_cell}"

                    rows.append({
                        "issue_no": issue_no,
                        "issue": issue_title,
                        "narrative": remove_action_taken(narrative),
                        "recommendation1": normalize_recommendation(rec_cell),
                        "recommendation2": "None",
                        "explanation": extract_explanation_from_narrative(narrative),
                        "correction": extract_correction_from_text(finding_cell),
                    })

    pdf_file.seek(0)

    if rows:
        # Sort by actual issue number to preserve report order.
        try:
            rows = sorted(rows, key=lambda x: int(x["issue_no"]))
        except Exception:
            pass
        return rows

    # Fallback: previous text-based logic if tables are not detected.
    text = extract_all_text(pdf_file)
    body = crop_report_body(text)
    lines = [x.rstrip() for x in body.split("\n") if clean_text(x)]
    entries = find_issue_title_entries(lines)
    fallback_rows = []

    for idx, entry in enumerate(entries):
        next_start = entries[idx + 1]["start"] if idx + 1 < len(entries) else len(lines)
        segment_lines = lines[entry["start"]:next_start]
        segment = "\n".join(segment_lines)
        issue_title = entry["title"]
        narrative_segment = "\n".join(lines[entry["end_title"]:next_start])

        fallback_rows.append({
            "issue_no": str(idx + 1),
            "issue": issue_title,
            "narrative": remove_action_taken(narrative_segment),
            "recommendation1": extract_recommendation_from_segment(segment),
            "recommendation2": "None",
            "explanation": extract_explanation_from_narrative(narrative_segment),
            "correction": extract_correction_from_text(segment),
        })

    return fallback_rows

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

        # Keep Issue Detail Issue as the exact captured issue title.
        issue_detail = item["issue"]

        # Make supporting fields concise while preserving the original audit thought.
        explanation = concise_text(item.get("explanation", "None"), "explanation", 25)
        recommendation1, recommendation2 = split_recommendation_fields(item.get("recommendation1", "None"))
        if item.get("recommendation2") and item.get("recommendation2") != "None":
            recommendation2 = concise_text(item.get("recommendation2"), "recommendation", 24)
        correction = concise_text(item.get("correction", "None"), "correction", 22)

        rows.append([
            row_no, date.today().isoformat(), audit_type, header["date_reported"],
            header["audit_reference"], emp_id, emp_name, task_id or "None",
            header["scope_date"], header["year"], findings,
            issue_detail,
            explanation, recommendation1,
            recommendation2, auditor or "None", "None",
            reaction, frequency, correction, "", case_status,
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