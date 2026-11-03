"""Stage the December 2025 NFOŚiGW ranking, never infer battery technology.

Input is the ten-column table extracted from the official PDF. Funding rows are
not project identities: grant/loan pairs and multi-site proposals need review.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Any


def _money(value: str) -> float | None:
    if re.fullmatch(r"-+", value):
        return None
    if not re.fullmatch(r"\d{1,3}(?: \d{3})*,\d{2}|\d+,\d{2}", value):
        raise ValueError(f"Unexpected PLN amount: {value!r}")
    return float(Decimal(value.replace(" ", "").replace(",", ".")))


def parse_ranking(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate table cells and expose candidates without merging or importing."""
    output = []
    identifiers: set[str] = set()
    for expected_rank, row in enumerate(rows, 1):
        cells = row["cells"]
        if len(cells) != 10 or cells[0] != str(expected_rank):
            raise ValueError("Changed columns, missing rank, or duplicate rank")
        rank, form, application, applicant, title, region, cost, asked, offered, points = cells
        if form not in {"Dotacja", "Pożyczka"}:
            raise ValueError("Unknown funding form")
        if not re.fullmatch(r"\d+/2025", application) or application in identifiers:
            raise ValueError("Duplicate or unexpected application identity")
        if not all([applicant, title, region]) or not points.isdigit() or row["page"] < 1:
            raise ValueError("Missing identity, page or score")
        identifiers.add(application)
        output.append(
            {
                "rank": int(rank),
                "page": row["page"],
                "application_id": application,
                "funding_form": form,
                "applicant": applicant,
                "source_title": title,
                "region": region,
                "total_cost_pln": _money(cost),
                "requested_funding_pln": _money(asked),
                "recommended_funding_pln": _money(offered),
                "score": int(points),
                "battery_explicit_in_title": bool(re.search(r"bater|\bBESS\b", title, re.I)),
                "status": "announced",
                "status_as_of": "2025-12-12",
                "review_required": True,
            }
        )
    if not output:
        raise ValueError("Empty ranking")
    return output
