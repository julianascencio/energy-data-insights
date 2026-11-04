"""Stage reviewed AJ stationary battery inverter tables, without canonical writes.

AJ converts DC to AC only. VA is apparent power; optional solar charging does
not establish bidirectional AC conversion. Responsive copies must agree.
"""

from __future__ import annotations

import hashlib
from typing import Any

from .studer import _match, _ProductHTML

MODELS = {
    "275-400": ["aj 275-12", "aj 350-24", "aj 400-48"],
    "500-700": ["aj 500-12", "aj 600-24", "aj 700-48"],
    "1000-1300": ["aj 1000-12", "aj 1300-24"],
    "2100-2400": ["aj 2100-12", "aj 2400-24"],
}


def parse_aj_html(content: bytes, series: str) -> list[dict[str, Any]]:
    """Require exact identities, table counts, units and conditional footnotes."""
    if series not in MODELS:
        raise ValueError("Unreviewed AJ series")
    parser = _ProductHTML()
    parser.feed(content.decode("utf-8-sig"))
    expected = MODELS[series]
    if parser.titles != expected or len(parser.blocks) != len(expected):
        raise ValueError("Changed exact model headings")
    count = 3 * len(expected)
    if len(parser.tables) != 2 * count or parser.tables[:count] != parser.tables[count:]:
        raise ValueError("Responsive tables disagree or table count changed")
    out = []
    num = r"([0-9]+(?:\.[0-9]+)?)"
    for i, model in enumerate(expected):
        pairs = [row for table in parser.tables[i * 3 : i * 3 + 2] for row in table]
        if len(pairs) != 17 or any(len(row) != 2 for row in pairs):
            raise ValueError("Changed AJ table shape")
        data = dict(pairs)
        if len(data) != 17:
            raise ValueError("Duplicate field")
        block = " ".join(parser.blocks[i].split())
        for required in [
            "IP30",
            "-20 to 50°C",
            "-1.5% / °C from + 25°C",
            "forced from 45°C ± 5°C",
            "120Vac/60Hz on request",
        ]:
            if required not in block:
                raise ValueError(f"Missing reviewed footnote: {required}")
        if series == "275-400" and "Standby with solar option -S" not in block:
            raise ValueError("Missing conditional standby footnote")
        try:
            dc = tuple(
                map(
                    float,
                    _match(
                        num + r" Vdc \(" + num + " \u2013 " + num + r" Vdc\)",
                        data["Nominal battery voltage (Input range)"],
                    ),
                )
            )
            power = {
                key: float(_match(num + " VA", data[label])[0])
                for key, label in [
                    ("continuous_va", "Continuous power 25°C"),
                    ("30min_va", "Power 30 min. 25°C"),
                    ("5min_va", "Power 5 min. 25°C"),
                    ("5sec_va", "Power 5 sec. 25°C"),
                ]
            }
            dims = list(
                map(
                    float,
                    _match(num + "/" + num + "/" + num + " mm", data["Dimensions h/w/l [mm]"]),
                )
            )
            weight = float(_match(num + " kg", data["Weight"])[0])
            efficiency = float(_match(num + "%", data["Max. efficiency (%)"])[0])
            idle = list(
                map(
                    float,
                    _match(
                        num + r" W(?:\*\*)?/ " + num + " W",
                        data["Consumption Stand-by / ON no load"],
                    ),
                )
            )
            short = list(
                map(
                    float,
                    _match(
                        num + r" Aac \(" + num + r" Aac\*\)",
                        data["Short-circuit current AC 2 sec."],
                    ),
                )
            )
        except KeyError as exc:
            raise ValueError(f"Missing expected field: {exc}") from exc
        if not 0 < dc[1] < dc[0] < dc[2] or not 0 < efficiency <= 100:
            raise ValueError("Invalid voltage or efficiency")
        if int(model.rsplit("-", 1)[1]) != dc[0]:
            raise ValueError("Nominal voltage disagrees with exact model")
        if any(x < 0 for x in idle):
            raise ValueError("Negative auxiliary consumption")
        if any(x <= 0 for x in [*power.values(), *dims, weight, *short]):
            raise ValueError("Nonpositive rating")
        out.append(
            dict(
                model=model,
                dc_nominal_v=dc[0],
                dc_min_v=dc[1],
                dc_max_v=dc[2],
                apparent_power_25c=power,
                dimensions_h_w_l_mm=dims,
                weight_kg=weight,
                maximum_inverter_efficiency_pct=efficiency,
                standby_on_no_load_w=idle,
                standby_requires_solar_option=series == "275-400",
                short_circuit_2sec_aac_230v_120v=short,
                reverse_polarity_protection=data["Reverse polarity protection as internal fuse"],
                source_sha256=hashlib.sha256(content).hexdigest(),
                locator=f"Technical data > {model}; inverter/general tables and footnotes",
            )
        )
    return out
