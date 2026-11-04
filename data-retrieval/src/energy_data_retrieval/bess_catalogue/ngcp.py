"""Offline staging of battery rows in NGCP bulletins 2026-19 and 2026-51.

This parser is revision-specific. It stages services, not plant operation or
capacity. BSS means black start service, not battery technology. Company aliases
and plant/phase reconciliation require a separate reviewed ledger.
"""

from __future__ import annotations

import re
from typing import Any

SOURCE_URL = (
    "https://www.ngcp.ph/Attachment-Uploads/"
    "Customer%20Bulletin%20Nos-2026-04-10-08-44-31.%202026-19.pdf"
)
SEPTEMBER_URL = (
    "https://www.ngcp.ph/Attachment-Uploads/"
    "Customer%20Bulletin%20Nos-2026-09-29-14-42-56.%202026-51.pdf"
)
BATTERY_NAMES = (
    "Alaminos 2 Battery Energy Storage System",
    "Advancion Energy Storage Array (Phase 1)",
    "San Manuel Battery Energy Storage System",
    "Lamao Battery Energy Storage System",
    "Bataan Battery Energy Storage System",
    "Concepcion Battery Energy Storage System",
    "Kabankalan Battery Energy Storage System",
    "Ubay Battery Energy Storage System",
    "Ormoc Battery Energy Storage System",
    "Toledo Battery Energy Storage System",
    "Jasaan Battery Energy Storage System",
    "Malita Battery Energy Storage System",
    "Maco Battery Energy Storage System",
    "Bac-Man BESS",
    "Alaminos 1 Battery Energy Storage System",
    "Gamu BESS",
    "Lumban BESS",
    "Magat BESS",
    "Southern Negros BESS",
    "Tongonan BESS",
    "Villanueva BESS",
)
SEPTEMBER_NAMES = (
    *(
        name
        for name in BATTERY_NAMES
        if name not in {"Gamu BESS", "Lumban BESS", "Villanueva BESS"}
    ),
    "Lumban Battery Energy Storage System",
    "Sangali Battery Energy Storage System",
    "Makban-Bay Geothermal Power Plant w/ BESS Unit 2",
    "Carmen BESS",
)


def parse_ngcp_batteries(content: bytes, *, source_url: str) -> list[dict[str, Any]]:
    """Stage the reviewed partition; newer editions require explicit review."""
    if source_url not in {SOURCE_URL, SEPTEMBER_URL}:
        raise ValueError("Expected reviewed NGCP bulletin URL")
    september = source_url == SEPTEMBER_URL
    names = SEPTEMBER_NAMES if september else BATTERY_NAMES
    text = content.decode("utf-8-sig")
    for marker in (
        "28 September 2026" if september else "01 April 2026",
        "AS OF SEPTEMBER 2026" if september else "AS OF MARCH 2026",
        "LIST OF AS CERTIFIED PLANTS WITH NO ASPA",
        "With filed Motion for Termination of the ASPA"
        if september
        else "Currently not providing their contracted Firm AS capacity",
        "BSS-Black Start Service",
    ):
        if marker not in text:
            raise ValueError(f"Missing reviewed bulletin marker: {marker}")
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    section = "existing_provider"
    page = 1
    for line in text.split("\n"):
        page += line.count("\f")
        if "LIST OF AS CERTIFIED PLANTS WITH NO ASPA" in line:
            section = "certified_no_aspa"
        if re.search(r"\bBESS\b|Battery Energy Storage|Energy Storage Array", line) and not any(
            name in line for name in names
        ):
            raise ValueError("Unreviewed battery row or changed line wrapping")
        for name in names:
            if name not in line:
                continue
            if name in seen:
                raise ValueError(f"Duplicate battery row: {name}")
            seen.add(name)
            tail = line.split(name, 1)[1].strip()
            match = re.fullmatch(
                r"(\*\*\*\s*)?((?:RR|CR|RPS)(?:,\s*(?:RR|CR|RPS))*)"
                r"(?:\s+(\d{4}-\d{3} RC))?",
                tail,
            )
            if not match:
                raise ValueError(f"Unrecognized services/case layout: {name}")
            warning, codes, case = match.groups()
            if (section == "existing_provider") != bool(case):
                raise ValueError("Case number inconsistent with bulletin section")
            rows.append(
                {
                    "plant_name": name,
                    "section": section,
                    "service_codes": codes.replace(" ", "").split(","),
                    "erc_case": case,
                    "not_providing_contracted_firm_capacity": bool(warning),
                    "reporting_date": "2026-09-28" if september else "2026-03-31",
                    "date_basis": "publication_date" if september else "reporting_period_end",
                    "warning_scope": "Footnote presence only; absence does not prove delivery",
                    "source_url": source_url,
                    "locator": f"PDF page {page}, {section}, {name} row",
                }
            )
    if seen != set(names):
        raise ValueError("Incomplete reviewed battery partition")
    return rows
