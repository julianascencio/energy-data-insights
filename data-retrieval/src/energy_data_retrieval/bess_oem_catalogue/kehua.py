"""Offline parser for Kehua's explicit model tabs; no family extrapolation.

The public HTML specification panels are the source, not linked PDF claims.
Fail closed on changed panel counts, duplicate labels, unsupported units or models.
"""

from __future__ import annotations

import re
from html import unescape
from typing import Any


def parse_kehua_html(content: bytes, *, expected_models: list[str]) -> list[dict[str, Any]]:
    """Stage exact panels with native labels and typed ratings; no canonical writes."""
    if len(content) > 5_000_000:
        raise ValueError("Kehua HTML exceeds size limit")
    text = content.decode("utf-8-sig")
    headers = re.findall(r'<div class="xx_xh">\s*((?:<a[^>]*>.*?</a>\s*)+)</div>', text, re.S)
    if len(headers) != 1:
        raise ValueError("Expected one exact-model tab header")
    models = [unescape(x).strip() for x in re.findall(r"<a[^>]*>(.*?)</a>", headers[0], re.S)]
    if models != expected_models or len(set(models)) != len(models) or not models:
        raise ValueError("Unexpected or duplicate model tabs")
    panels = re.findall(r'<div class="info_list[^\"]*">(.*?)<div class="g-btn-red">', text, re.S)
    if len(panels) != len(models):
        raise ValueError("Model/panel count mismatch")
    results = []
    for model, panel in zip(models, panels, strict=True):
        pairs = re.findall(
            r'<div class="attr_item"\s*>\s*<p>(.*?)</p>\s*<p>(.*?)</p>\s*</div>', panel, re.S
        )
        fields = {unescape(k).strip(): unescape(v).strip() for k, v in pairs}
        if len(fields) != len(pairs) or len(pairs) != panel.count('class="attr_item"'):
            raise ValueError("Duplicate or malformed specification field")
        central = {
            "Max. DC current",
            "Rated AC output power",
            "Rated grid-tied voltage",
            "Grid frequency range",
            "Max. output current",
            "Adjustable power factor",
            "IP rating",
        }
        modular = {
            "DC full load voltage range",
            "Rated output voltage",
            "Rated AC output power",
            "IP rating",
        }
        legacy = {
            "MAX. DC voltage",
            "DC voltage range",
            "Max. DC current",
            "Max. AC output power",
            "Max. efficiency",
        }
        if set(fields) not in [
            central,
            modular | {"Grid frequency range"},
            modular | {"Rated AC Frequency"},
            legacy,
        ]:
            raise ValueError("Unsupported specification layout")
        numeric: dict[str, Any] = {}
        for label, unit, key in [
            ("Max. DC current", "A", "maximum_dc_current_a"),
            ("Max. output current", "A", "maximum_ac_current_a"),
            ("MAX. DC voltage", "Vdc", "absolute_maximum_dc_voltage_v"),
            ("Max. AC output power", "kVA", "maximum_apparent_power_kva"),
            ("Max. efficiency", "%", "maximum_conversion_efficiency_pct"),
        ]:
            if label in fields:
                match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)" + unit, fields[label])
                if not match or float(match[1]) <= 0:
                    raise ValueError("Invalid value or unit: " + label)
                numeric[key] = float(match[1])
        if "Rated AC output power" in fields:
            match = re.fullmatch(
                r"([0-9]+(?:\.[0-9]+)?)kW(?:@(\d+)°C)?", fields["Rated AC output power"]
            )
            if not match:
                raise ValueError("Invalid active-power rating or conditions")
            numeric["rated_ac_power_kw"] = float(match[1])
            if match[2]:
                numeric["rated_power_temperature_c"] = float(match[2])
        for label in ["DC voltage range", "DC full load voltage range"]:
            if label in fields:
                match = re.fullmatch(r"(\d+)~(\d+)Vdc", fields[label])
                if not match or int(match[1]) >= int(match[2]):
                    raise ValueError("Invalid voltage range")
                numeric["dc_voltage_range_v"] = [int(match[1]), int(match[2])]
                numeric["voltage_range_basis"] = (
                    "full_load" if "full load" in label else "operating"
                )
        for label in ["Rated output voltage", "Rated grid-tied voltage"]:
            if label in fields:
                match = re.fullmatch(r"(\d+)Vac\s*(3P3W(?:\+PE)?)", fields[label])
                if not match:
                    raise ValueError("Invalid AC voltage/wiring")
                numeric["rated_ac_voltage_v"] = int(match[1])
                numeric["ac_wiring"] = match[2]
        results.append({"model": model, "native_fields": fields, "numeric": numeric})
    return results
