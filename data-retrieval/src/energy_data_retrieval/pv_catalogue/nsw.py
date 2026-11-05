"""Read checksum-pinned NSW planning tracker metadata for identity review.

Solar Farm is a publisher category, not positive PV proof. These rows are review
candidates; an existing positively identified PV project and a reviewed identity
are required before upsert. Planning capacity, storage and status remain native
historical assertions and never become operating nameplates or lifecycle fields.
"""

import hashlib
import re
from collections import Counter
from datetime import date, datetime
from html.parser import HTMLParser
from typing import Any

_COLUMNS = {
    "Project",
    "Project type",
    "Status",
    "Location",
    "Renewable Energy Zone",
    "Generating capacity (MW)",
    "Storage capacity (MW/MWh)",
    "Modifications",
    "Number of households capable of being powered",
    "Carbon emissions avoided in first year (Tonnes CO2e)",
    "Potential number of jobs created",
    "Approval date",
    "Approved by",
    "Referred to Independent Planning Commission",
}


class _Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = []

    def handle_data(self, data: str) -> None:
        self.text.append(data)
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None:
            if self.row is not None:
                self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def read_nsw_renewable_tracker(data: bytes, *, sha256: str, as_of: str) -> list[dict[str, Any]]:
    """Stage all Solar Farm cards, preserving duplicate names as review flags."""
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("NSW tracker checksum mismatch")
    snapshot = date.fromisoformat(as_of)
    parser = _Tables()
    parser.feed(data.decode("utf-8"))
    text = " ".join(" ".join(parser.text).split())
    match = re.search(r"This table was last updated on (\d{1,2} [A-Za-z]+ \d{4})", text)
    if not match or datetime.strptime(match[1], "%d %B %Y").date() != snapshot:
        raise ValueError("NSW tracker as-of date mismatch")
    groups: list[dict[str, str]] = []
    group: dict[str, str] | None = None
    for row in parser.rows:
        if len(row) == 2 and row[0] == "Project":
            if group:
                groups.append(group)
            group = {"Project": row[1]}
        elif group is not None and len(row) == 2:
            if row[0] in group:
                raise ValueError("Duplicate NSW card column")
            group[row[0]] = row[1]
    if group:
        groups.append(group)
    summary = Counter(
        tuple(row[:3]) for row in parser.rows if len(row) == 4 and row[0] != "Project"
    )
    details = Counter((g["Project"], g.get("Project type"), g.get("Status")) for g in groups)
    if not summary or summary != details:
        raise ValueError("NSW summary/detail inventory mismatch")
    solar = [g for g in groups if g.get("Project type") == "Solar Farm"]
    if not solar:
        raise ValueError("No NSW Solar Farm review candidates")
    names = Counter(g["Project"] for g in solar)
    result = []
    for number, g in enumerate(solar, 1):
        if set(g) != _COLUMNS or not g["Project"] or not g["Location"]:
            raise ValueError("Unexpected NSW card schema")
        if g["Status"] not in {"Approved", "Operational", "Under assessment"}:
            raise ValueError("Unknown NSW historical planning status")
        approved = None
        if g["Approval date"] == "N/A" and g["Status"] == "Under assessment":
            pass
        else:
            approved = datetime.strptime(g["Approval date"], "%d/%m/%Y").date()
        if approved and approved > snapshot:
            raise ValueError("NSW approval after tracker as-of date")
        result.append(
            {
                "solar_card_number": number,
                "project_name": g["Project"],
                "source_name_count": names[g["Project"]],
                "publisher_category": g["Project type"],
                "as_of": as_of,
                "source_status": g["Status"],
                "source_location": g["Location"],
                "renewable_energy_zone": g["Renewable Energy Zone"],
                "generating_capacity_native": g["Generating capacity (MW)"],
                "generating_capacity_basis": "Unspecified AC/DC; planning tracker assertion",
                "storage_capacity_native": g["Storage capacity (MW/MWh)"],
                "modifications_native": g["Modifications"],
                "approval_date_native": g["Approval date"],
                "approval_date": approved.isoformat() if approved else None,
                "approved_by": g["Approved by"],
                "ipc_referral_native": g["Referred to Independent Planning Commission"],
                "review_status": "Unaccepted; positive PV and plant/phase identity review required",
            }
        )
    return result


class _PermitText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[str] = []
        self.heading: list[str] = []
        self.skip = 0
        self.in_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.skip += 1
        if tag == "h1":
            self.in_heading = True

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.skip -= 1
        if tag == "h1":
            self.in_heading = False

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if value and not self.skip:
            self.tokens.append(value)
            if self.in_heading:
                self.heading.append(value)


def read_nsw_project_page(data: bytes, *, sha256: str) -> dict[str, Any]:
    """Stage bounded departmental permit metadata, never submissions or contacts.

    A solar application category does not prove PV, operation, capacity basis or
    plant identity. Modifications remain separate application metadata.
    """
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("NSW permit checksum mismatch")
    parser = _PermitText()
    parser.feed(data.decode("utf-8"))
    tokens = parser.tokens
    if len(parser.heading) != 1 or tokens.count("Project Details") != 1:
        raise ValueError("Ambiguous NSW permit heading/details")
    start = tokens.index("Project Details") + 1
    stops = [i for i in range(start, len(tokens)) if tokens[i].startswith("Contact")]
    if not stops:
        raise ValueError("Missing NSW permit contact boundary")
    details = tokens[start : stops[0]]
    fields = {
        "Application Number": "application_id",
        "EPBC ID Number": "epbc_referral_id",
        "Assessment Type": "assessment_type",
        "Development Type": "development_type",
        "Local Government Areas": "local_government_area",
        "Decision": "decision",
        "Determination Date": "determination_date",
        "Decider": "decider",
        "Last Modified By": "last_modified_application",
        "Last Modified On": "last_modified_on",
    }
    result: dict[str, Any] = {"project_name": parser.heading[0]}
    positions = [(i, t) for i, t in enumerate(details) if t in fields]
    if not positions or positions[0] != (0, "Application Number"):
        raise ValueError("Unknown NSW permit detail layout")
    for n, (i, label) in enumerate(positions):
        end = positions[n + 1][0] if n + 1 < len(positions) else len(details)
        values = details[i + 1 : end]
        key = fields[label]
        if key in result or len(values) != 1:
            raise ValueError("Duplicate or malformed NSW permit field")
        result[key] = values[0]
    if not {"application_id", "assessment_type", "local_government_area"} <= result.keys():
        raise ValueError("Missing NSW permit identity fields")
    if not re.fullmatch(
        r"(?:SSD-\d+(?:-[Mm][Oo][Dd]-\d+)?|MP_?\d{2}_\d{4})", result["application_id"]
    ):
        raise ValueError("Unknown NSW application identifier")
    for key in ("determination_date", "last_modified_on"):
        if key in result:
            result[key] = datetime.strptime(result[key], "%d/%m/%Y").date().isoformat()
    if "epbc_referral_id" in result and not re.fullmatch(
        r"\d{4}/\d{4,5}", result["epbc_referral_id"]
    ):
        raise ValueError("Unknown EPBC referral identifier")
    result["is_modification"] = "-mod-" in result["application_id"].lower()
    result["review_status"] = (
        "Unaccepted permit metadata; positive PV and project identity review required"
    )
    result["scope"] = (
        "Departmental Project Details only; no submissions, contacts, operation or AC/DC inference"
    )
    return result
