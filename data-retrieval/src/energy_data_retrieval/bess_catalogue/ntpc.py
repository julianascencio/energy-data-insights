"""Stage two reviewed NTPC IFB tables; tender rows are not operating projects."""

from __future__ import annotations

import hashlib
import re
from typing import Any


def parse_ntpc_ifb(content: bytes, *, lot: int) -> list[dict[str, Any]]:
    """Read local pdftotext-layout output for the 2025 Lot-1/2 notices.

    Enforce revision, units, complete row numbering, within-table identity and
    capacity controls. No network, canonical writes, site merges, MW inference,
    lifecycle promotion or reuse permission is provided by this staging helper.
    The digest describes extracted text, never the original PDF.
    """
    specs = {
        1: ("2025_NTPC_100673_1", "CS-0011-171A-9", "30.09.2025", 7, 2334),
        2: ("2025_NTPC_101702_1", "CS-0011-171B-9", "06.11.2025", 9, 2670),
    }
    if lot not in specs:
        raise ValueError("Unreviewed lot")
    tender, document, date, count, total = specs[lot]
    text = content.decode("utf-8-sig")
    if not all(marker in text for marker in (tender, document, date, f"(Lot-{lot})")):
        raise ValueError("Unreviewed notice identity or date")
    page = text.split("\f")[0]
    section = re.search(
        rf"Lot-{lot} comprises.*?following Stations/projects:(.*?)\n\s*2\.0", page, re.S
    )
    if section is None:
        raise ValueError("Missing table boundary")
    table = section.group(1)
    header = table.split("1", 1)[0]
    if not all(marker in header for marker in ("Battery", "Capacity", "(MWh)")):
        raise ValueError("Expected battery MWh header")
    starts = list(re.finditer(r"(?m)^\s*(\d+)\.?\s+(?=[A-Z])", table))
    if [int(m[1]) for m in starts] != list(range(1, count + 1)):
        raise ValueError("Incomplete or repeated row numbering")
    rows: list[dict[str, Any]] = []
    seen = set()
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(table)
        body = table[match.end() : end]
        ratings = list(re.finditer(r"(?m)\s{2,}(\d+(?:\.\d+)?)\s*$", body))
        if len(ratings) != 1:
            raise ValueError("Ambiguous battery capacity")
        rating = ratings[0]
        name = " ".join((body[: rating.start()] + " " + body[rating.end() :]).split())
        energy = float(rating[1])
        if not name or name.casefold() in seen or energy <= 0:
            raise ValueError("Duplicate site or invalid rating")
        seen.add(name.casefold())
        rows.append(
            {
                "source_name": name,
                "lot": lot,
                "source_row": index + 1,
                "source_page": 1,
                "tender_id": tender,
                "document_id": document,
                "source_date": "-".join(reversed(date.split("."))),
                "tender_battery_energy_mwh": energy,
                "energy_basis": "unspecified",
                "status": "announced",
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    if sum(r["tender_battery_energy_mwh"] for r in rows) != total:
        raise ValueError("Reviewed table capacity control changed")
    return rows
