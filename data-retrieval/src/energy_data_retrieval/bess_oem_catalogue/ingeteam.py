"""Offline staging of three reviewed Ingeteam battery-converter datasheets.

No identities are imported. kVA stays apparent power; voltage operating points
of the 350TL remain one model. Common specifications require visual review.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


def _between(text: str, start: str, end: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        raise ValueError(f"Missing or repeated table boundary: {start}")
    return text.split(start)[1].split(end)[0]


def _numbers(text: str, count: int, suffix: str = "") -> list[int]:
    pattern = r"(?<![\w.])([\d,]+)" + suffix
    values = [int(x.replace(",", "")) for x in re.findall(pattern, text)]
    if len(values) != count or any(x <= 0 for x in values):
        raise ValueError("Unexpected numeric column count or nonpositive value")
    return values


def parse_converter_text(content: bytes, series: str) -> list[dict[str, Any]]:
    """Stage reviewed revisions M/C/350; reject unit, heading and shape changes."""
    pages = content.decode("utf-8-sig").split("\f")
    revisions = {"M": "300002287_C", "C": "300001994/F", "350": "300002273_A"}
    if series not in revisions or revisions[series] not in " ".join(pages):
        raise ValueError("Unreviewed series or revision")
    expected = {"M": "4540TL", "C": "3930TL HV", "350": "350TL"}[series]
    if expected not in " ".join(pages):
        raise ValueError("Missing exact converter model heading")
    out: list[dict[str, Any]] = []
    if series == "M":
        table = pages[3] if len(pages) > 3 else ""
        if not re.search(r"M600\s+M630\s+M660\s+M690", table):
            raise ValueError("Changed M configuration headers")
        if not re.search(r"INPUT \(DC\)\s+" + r"M3\s+M4\s+" * 3 + r"M3\s+M4", table):
            raise ValueError("Changed module configuration order")
        power = _numbers(_between(table, "(40 °C)[kVA]", "Discharge/charge current"), 8)
        current = _numbers(
            _between(table, "Discharge/charge current (40 °C) [A]", "AC output voltage"), 8
        )
        ranges = re.findall(
            r"([\d,]+) to 1,500", _between(table, "INPUT (DC)", "Nº DC inputs per module")
        )
        if len(ranges) != 8:
            raise ValueError("Changed M DC voltage envelopes")
        for i in range(8):
            j = i // 2
            out.append(
                dict(
                    model="INGECON SUN STORAGE 4540TL",
                    configuration=f"M{[600, 630, 660, 690][j]} M{3 + i % 2}",
                    ac_voltage_v=[600, 630, 660, 690][j],
                    modules=3 + i % 2,
                    charge_discharge_kva=power[i],
                    ac_current_a=current[i],
                    rated_temperature_c=40,
                    off_grid_dc_min_v=int(ranges[j].replace(",", "")),
                    grid_tied_dc_min_v=int(ranges[4 + j].replace(",", "")),
                    locator=f"PDF p4 column {i + 1}",
                )
            )
    elif series == "C":
        table = pages[2] if len(pages) > 2 else ""
        voltages = [600, 630, 660, 690, 720, 760, 840]
        if not re.search(r"\s+".join(f"C{v}" for v in voltages), table):
            raise ValueError("Changed C configuration headers")
        discharge = _numbers(
            _between(table, "Discharge power @1,500 Vdc", "Discharge current @1,500 Vdc"),
            14,
            r" kVA",
        )
        charge = _numbers(
            _between(table, "Charge power @1,500 Vdc", "Charge current @1,500 Vdc"), 14, r" kVA"
        )
        ranges = re.findall(r"([\d,]+) - 1,500 V", _between(table, "INPUT (DC)", "Maximum voltage"))
        if len(ranges) != 14 or "(30 °C/ 50 °C)" not in table:
            raise ValueError("Changed C voltage envelopes or temperatures")
        for i, voltage in enumerate(voltages):
            out.append(
                dict(
                    model="INGECON SUN STORAGE 3930TL HV",
                    configuration=f"C{voltage}",
                    ac_voltage_v=voltage,
                    discharge_kva_30c=discharge[i],
                    discharge_kva_50c=discharge[i + 7],
                    charge_kva_30c=charge[i],
                    charge_kva_50c=charge[i + 7],
                    rating_dc_voltage_v=1500,
                    off_grid_dc_min_v=int(ranges[i].replace(",", "")),
                    grid_tied_dc_min_v=int(ranges[i + 7].replace(",", "")),
                    locator=f"PDF p3 column {i + 1}",
                )
            )
    else:
        points = []
        for page, voltages in [(2, [600, 615, 630, 645, 660]), (3, [675, 690, 710, 730, 750, 800])]:
            table = pages[page] if len(pages) > page else ""
            if not re.search(r"\s+".join(f"{v} V" for v in voltages), table):
                raise ValueError("Changed 350TL operating-point headers")
            power = _numbers(
                _between(table, "Charge/Discharge power", "Charge/Discharge current"),
                len(voltages),
                r" kVA",
            )
            ranges = re.findall(
                r"([\d,]+) - 1,500 V", _between(table, "INPUT (DC)", "Maximum voltage")
            )
            if len(ranges) != len(voltages):
                raise ValueError("Changed 350TL voltage envelopes")
            points.extend(
                dict(
                    ac_voltage_v=v,
                    charge_discharge_kva=power[i],
                    dc_min_v=int(ranges[i].replace(",", "")),
                    locator=f"PDF p{page + 1} column {i + 1}",
                )
                for i, v in enumerate(voltages)
            )
        out.append(
            dict(
                model="INGECON SUN STORAGE 350TL",
                configuration="IEC variable AC voltage",
                operating_points=points,
                locator="PDF pp3-4; one model, eleven voltage-dependent operating points",
            )
        )
    for row in out:
        row.update(
            document_revision=revisions[series],
            extracted_text_sha256=hashlib.sha256(content).hexdigest(),
            active_power_not_inferred=True,
        )
    return out
