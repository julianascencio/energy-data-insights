"""Bounded, privacy-minimal MaStR 26.2 solar-unit review staging.

Read extracted UTF-8 EinheitenSolar XML, never whole-project records. Pin the
original archive checksum before resuming a physical-row cursor. No network
requests, canonical upserts, status inference, aggregation or AC/DC conversion.
Mapping: BNetzA Gesamtdatenexport revision 26.2 (1 October 2026), section 5.5.2
and EinheitenSolar.xsd. Names, operators and addresses are deliberately omitted.
"""

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import BinaryIO
from xml.etree import ElementTree as ET

_POWER_FIELDS = ("Bruttoleistung", "Nettonennleistung", "ZugeordneteWirkleistungWechselrichter")
_FIELDS = (
    "EinheitMastrNummer",
    "LokationMaStRNummer",
    "EegMaStRNummer",
    "DatumLetzteAktualisierung",
    "NetzbetreiberpruefungStatus",
    "NetzbetreiberpruefungDatum",
    *_POWER_FIELDS,
)


class _DtdFreeReader:
    def __init__(self, stream: BinaryIO):
        self.stream = stream
        self.tail = b""

    def read(self, size: int = -1) -> bytes:
        data = self.stream.read(size)
        scan = self.tail + data
        if b"\x00" in scan or b"<!DOCTYPE" in scan.upper():
            raise ValueError("Only DTD-free UTF-8 official XML is supported")
        self.tail = scan[-9:]
        return data


def read_mastr_solar_units(
    path: Path, *, start_row: int = 0, limit: int = 1000
) -> list[dict[str, str | int | None]]:
    """Stage at most 10,000 units; row offsets require an unchanged source hash.

    Preserve native field labels and numeric strings. Bruttoleistung and
    Nettonennleistung are documented in kW; the allocated inverter-power row's
    unit is not explicit in the inspected definition, so it remains native.
    Review-status codes are retained without a reviewed/unreviewed inference.
    Duplicate unit IDs within a selected partition raise instead of merging.
    This is not full XSD validation or a production archive ingestion adapter.
    """
    if start_row < 0 or not 1 <= limit <= 10_000:
        raise ValueError("Require nonnegative start_row and limit in 1..10000")
    selected = []
    seen = set()
    with path.open("rb") as stream:
        events = ET.iterparse(_DtdFreeReader(stream), events=("start", "end"))
        _, root = next(events)
        if root.tag != "EinheitenSolar":
            raise ValueError("Expected explicit EinheitenSolar technology partition")
        position = 0
        for event, node in events:
            if event != "end" or node.tag != "EinheitSolar":
                continue
            position += 1
            if position <= start_row:
                root.remove(node)
                continue
            values = {}
            for child in node:
                if child.tag in _FIELDS:
                    if child.tag in values:
                        raise ValueError(f"Repeated field: {child.tag}")
                    values[child.tag] = (child.text or "").strip() or None
            identifier = values.get("EinheitMastrNummer")
            if not identifier or identifier in seen:
                raise ValueError("Missing or duplicate selected unit ID")
            seen.add(identifier)
            for key in _POWER_FIELDS:
                value = values.get(key)
                if value is None:
                    continue
                try:
                    number = Decimal(value)
                except InvalidOperation as exc:
                    raise ValueError(f"Invalid native power: {key}") from exc
                if not number.is_finite() or number < 0:
                    raise ValueError(f"Nonfinite or negative native power: {key}")
            selected.append({"source_row": position, **dict.fromkeys(_FIELDS), **values})
            root.remove(node)
            if len(selected) == limit:
                break
    return selected
