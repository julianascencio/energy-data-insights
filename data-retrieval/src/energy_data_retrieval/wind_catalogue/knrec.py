"""Checksum-pinned Korean certification register extraction; no validity inference."""

from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser


class _Rows(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self.row: list[str] = []
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"}:
            self.cell = []
        if tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        if tag == "tr" and self.row:
            self.rows.append(self.row)


def certification_rows(original: bytes, *, sha256: str) -> dict[str, list[str]]:
    """Return exact register cells by certificate ID; keep ranges and conflicts raw.

    A listing is a dated registry observation, not an independently verified
    certificate or evidence of current eligibility. No power/hub Cartesian expansion.
    """
    if hashlib.sha256(original).hexdigest() != sha256:
        raise ValueError("Register checksum mismatch")
    parser = _Rows()
    parser.feed(original.decode("utf-8"))
    result: dict[str, list[str]] = {}
    for row in parser.rows:
        if len(row) > 1 and row[1].startswith("WT-"):
            if len(row) != 14 or row[1] in result:
                raise ValueError("Changed register shape or duplicate certificate ID")
            result[row[1]] = row
    if not result:
        raise ValueError("No certification rows")
    return result


def specification(row: list[str]) -> dict[str, object]:
    """Normalize a reviewed row, retaining multiple options without pairing them.

    This does not approve identity, resolve contradictory cells, or establish
    current certificate validity. Unitless and range values remain untyped.
    """
    if len(row) != 14 or not row[1].startswith("WT-"):
        raise ValueError("Expected fourteen certification cells")

    def options(value: str, unit: str, scale: float = 1) -> list[float]:
        match = re.fullmatch(
            r"\s*(\d+(?:\.\d+)?(?:\s*[,/]\s*\d+(?:\.\d+)?)*)\s*" + re.escape(unit), value
        )
        if not match:
            return []
        values = [float(v) * scale for v in re.split(r"\s*[,/]\s*", match[1])]
        if any(v <= 0 for v in values) or len(set(values)) != len(values):
            raise ValueError("Nonpositive or duplicate specification options")
        return values

    power = options(row[5], "MW", 1000)
    rotor = options(row[10], "m")
    hubs = options(row[11], "m")
    speeds = options(row[9], "m/s")
    return {
        "rating_options_kw": power,
        "rated_power_kw": power[0] if len(power) == 1 else None,
        "rotor_diameter_m": rotor[0] if len(rotor) == 1 else None,
        "hub_height_options_m": hubs,
        "hub_height_m": hubs[0] if len(hubs) == 1 else None,
        "rated_wind_speed_options_m_s": speeds,
        "rated_wind_speed_m_s": speeds[0] if len(speeds) == 1 else None,
        "gearbox_present": {"유": True, "무": False}.get(row[7]),
        "application": {"육상용": "onshore", "해상용": "offshore"}.get(row[8]),
        "registry_status": "expired"
        if row[13] == "만료"
        else "cancelled"
        if row[13].startswith("인증취소")
        else "unspecified",
        "current_validity": None,
    }
