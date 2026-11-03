"""Stage Flower's reviewed Q2 2026 named portfolio, without merging identities."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Any


def parse_flower_portfolio(content: bytes) -> list[dict[str, Any]]:
    """Read local pdftotext-layout output and validate its MW/MWh control totals.

    Report narrative in the right column is ignored. Dates are reporting-period
    observations, not COD. A row may still represent multiple physical assets:
    callers must review scope, notably Marieboda, before accepting records.
    """
    text = content.decode("utf-8-sig")
    if "Second quarter interim report 2026" not in text:
        raise ValueError("Unreviewed report period; expected Q2 2026")
    pages = text.split("\f")
    matching = [(i, p) for i, p in enumerate(pages, 1) if "Operational BESS assets" in p]
    if len(matching) != 1:
        raise ValueError("Expected one named portfolio table")
    page_number, page = matching[0]
    lines = page.splitlines()
    start = next(i for i, line in enumerate(lines) if "Operational BESS assets" in line)
    if not re.search(r"Size \(MW\)\s+Size \(MWh\)", lines[start]):
        raise ValueError("Unreviewed power/energy units")
    if sum(line.startswith("Assets under construction") for line in lines[start:]) != 1:
        raise ValueError("Missing or repeated construction section")
    state = "operational"
    rows: list[dict[str, Any]] = []
    names = set()
    for line in lines[start + 1 :]:
        if line.startswith("Assets under construction"):
            state = "under_construction"
            continue
        match = re.match(r"^(\S(?:.*?\S)?)\s{2,}([0-9.]+)\s+([0-9.]+)(?:\s|$)", line)
        if not match:
            continue
        name, mw_text, mwh_text = match.groups()
        mw, mwh = float(mw_text), float(mwh_text)
        if not all(math.isfinite(x) and x > 0 for x in (mw, mwh)):
            raise ValueError("Invalid capacity")
        if name == "Total":
            if not rows or any(
                not math.isclose(sum(r[key] for r in rows), target, abs_tol=0.001)
                for key, target in (("power_mw", mw), ("energy_mwh", mwh))
            ):
                raise ValueError("Portfolio totals do not reconcile")
            return rows
        if name in names:
            raise ValueError("Duplicate portfolio identity")
        names.add(name)
        rows.append(
            {
                "name": name,
                "power_mw": mw,
                "energy_mwh": mwh,
                "status": state,
                "status_as_of": "2026-06-30",
                "source_page": page_number,
                "source_row": len(rows) + 1,
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    raise ValueError("Missing control total")
