"""Offline staging of İzmir's licensed municipal PV portfolio CSV.

Rows are candidates, not canonical projects. Review identities and source release
before upsert. The broken XLSX export is not a fallback for this CSV edition.
"""

import csv
import hashlib
import io
from pathlib import Path

HEADERS = (
    "PROJE ADI",
    "TOPLAM PANEL SAYISI",
    "PANEL GÜCÜ (W)",
    "TOPLAM GÜÇ (kW)",
    "BEKLENEN YILLIK ÜRETİM\n(kWh)",
    "AÇIKLAMA",
)


def read_izmir_csv(path: Path, *, sha256: str) -> list[dict]:
    """Stage checksum-pinned native rows; reject drift, duplicates and bad numbers.

    No AC/DC, owner, coordinates, operating status or precise COD is inferred.
    Panel counts prove PV equipment; expected kWh is not measured generation.
    """
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != sha256:
        raise ValueError("İzmir checksum mismatch")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=";")
    if tuple(reader.fieldnames or ()) != HEADERS:
        raise ValueError("İzmir CSV header drift")
    staged = []
    seen = set()
    for row_number, row in enumerate(reader, 2):
        if None in row or any(v is None for v in row.values()):
            raise ValueError("İzmir CSV row width")
        name = row[HEADERS[0]].strip()
        if not name or name.casefold() in seen:
            raise ValueError("İzmir duplicate or empty project name")
        seen.add(name.casefold())
        numbers = {}
        for key in HEADERS[1:5]:
            raw = row[key].strip()
            value = None if raw == "-" else float(raw)
            if value is not None and (not 0 < value < 1e9):
                raise ValueError("İzmir invalid numeric value")
            numbers[key] = value
        count = numbers[HEADERS[1]]
        if count is not None and not count.is_integer():
            raise ValueError("İzmir noninteger panel count")
        power = numbers[HEADERS[3]]
        generation = numbers[HEADERS[4]]
        if power is None or generation is None:
            raise ValueError("İzmir missing power or expected generation")
        staged.append(
            {
                "source_row": row_number,
                "name": name,
                "module_count": int(count) if count is not None else None,
                "reported_module_power_w": numbers[HEADERS[2]],
                "capacity_unspecified_mw": power / 1000,
                "expected_annual_generation_mwh": generation / 1000,
                "native_status_note": row[HEADERS[5]].strip(),
                "identity_review_required": True,
            }
        )
    if not staged:
        raise ValueError("İzmir empty CSV")
    return staged
