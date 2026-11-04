"""Stage the EA 29 September 2026 BESS overview, without changing identities/status."""

import hashlib
import re
from typing import Any

from .pib import _Tables

HEADERS = ["BESS name/location", "Owner", "Capacity", "Connection type", "Commissioning status"]


def parse_ea_status_html(content: bytes) -> list[dict[str, Any]]:
    """Preserve commissioning text and owner labels; never synthesize exact COD.

    Later owner evidence can supersede this historical table. In particular,
    commissioning, committed and operating are different lifecycle observations.
    """
    text = content.decode("utf-8-sig")
    if "29 September 2026" not in text or "Status of BESS developments" not in text:
        raise ValueError("Unreviewed EA status release")
    parser = _Tables()
    parser.feed(text)
    matches = [t for t in parser.tables if t and t[0] == HEADERS]
    if len(matches) != 1:
        raise ValueError("Expected one reviewed status table")
    rows = matches[0][1:]
    if len(rows) != 6:
        raise ValueError("Expected six status observations")
    result = []
    seen = set()
    for ordinal, row in enumerate(rows, 1):
        if len(row) != 5 or not all(row) or row[0] in seen:
            raise ValueError("Malformed or duplicate project row")
        name, owner, capacity, connection, status = row
        seen.add(name)
        rating = re.fullmatch(r"(\d+)MW/(\d+)MWh \((\d+) hours? storage\)", capacity)
        if not rating or connection not in {"Grid connected", "Distribution network connected"}:
            raise ValueError("Unreviewed rating units or connection")
        if status not in {"Under construction", "Commissioning", "Committed"} and not re.fullmatch(
            r"Commissioned in (?:January|February|March|April|May|June|July|August|"
            r"September|October|November|December) 20\d{2}",
            status,
        ):
            raise ValueError("Unreviewed commissioning observation")
        mw, mwh, hours = map(float, rating.groups())
        if min(mw, mwh, hours) <= 0:
            raise ValueError("Nonpositive capacity/duration")
        result.append(
            dict(
                source_row=ordinal,
                name=name,
                owner_native=owner,
                power_mw=mw,
                energy_mwh=mwh,
                reported_duration_hours=hours,
                connection_native=connection,
                status_native=status,
                source_date="2026-09-29",
                source_sha256=hashlib.sha256(content).hexdigest(),
            )
        )
    return result
