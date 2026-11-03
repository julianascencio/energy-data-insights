"""Stage the dated CEB Mauritius battery table without inferring lifecycle."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any


def parse_ceb_battery_table(content: bytes) -> list[dict[str, Any]]:
    """Parse local pdftotext-layout output of the 26 May 2022 presentation.

    The first table has a six-site control total. A separate Amaury expansion
    must remain distinct from its earlier installation. Neither this parser nor
    the table establishes commissioning, usable energy, chemistry or AC basis.
    The checksum fingerprints extracted text, not the original PDF bytes.
    """
    text = content.decode("utf-8-sig")
    if not re.search(r"Date\s*:\s*26 May 2022", text):
        raise ValueError("Unreviewed presentation date")
    pages = [
        (i, p)
        for i, p in enumerate(text.split("\f"), 1)
        if "Battery Energy Storage System Project" in p
    ]
    if len(pages) != 1:
        raise ValueError("Expected one battery project table page")
    page_number, page = pages[0]
    headers = list(re.finditer(r"(?m)^\s*(\d+(?:\.\d+)?) MW / (\d+(?:\.\d+)?) MWh\s*$", page))
    if len(headers) != 2:
        raise ValueError("Expected separate portfolio and expansion sections with MW/MWh")
    rows: list[dict[str, Any]] = []
    for section, header in enumerate(headers):
        end = headers[section + 1].start() if section == 0 else len(page)
        body = page[header.end() : end]
        matches = list(
            re.finditer(
                r"(?m)^\s*([A-Za-z][A-Za-z ]*?)\s{2,}(\d+(?:\.\d+)?)\s*MW,\s*"
                r"(\d+(?:\.\d+)?)\s*MWh\s*$",
                body,
            )
        )
        if len(matches) != (6 if section == 0 else 1):
            raise ValueError("Missing, extra or unreviewed capacity rows")
        seen = set()
        batch: list[dict[str, Any]] = []
        for match in matches:
            name, power, energy = match.groups()
            name = " ".join(name.split())
            mw, mwh = float(power), float(energy)
            if name.casefold() in seen:
                raise ValueError("Duplicate site within section")
            seen.add(name.casefold())
            if not all(math.isfinite(x) and x > 0 for x in (mw, mwh)):
                raise ValueError("Invalid capacity")
            batch.append(
                {
                    "source_name": name,
                    "section": "six_site_portfolio" if section == 0 else "separate_expansion",
                    "power_mw": mw,
                    "energy_mwh": mwh,
                    "status": "unknown",
                    "source_date": "2022-05-26",
                    "source_page": page_number,
                    "source_row": len(batch) + 1,
                    "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
                }
            )
        for key, target in zip(("power_mw", "energy_mwh"), header.groups(), strict=True):
            if not math.isclose(sum(r[key] for r in batch), float(target), abs_tol=1e-8):
                raise ValueError("Section control total does not reconcile")
        if section == 1 and batch[0]["source_name"] != "Amaury":
            raise ValueError("Unreviewed expansion identity")
        rows.extend(batch)
    return rows
