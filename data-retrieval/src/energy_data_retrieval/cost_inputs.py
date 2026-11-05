"""Read an explicitly attributed, offline JWPA industry-cost scenario snapshot.

This is not a live METI or JWPA API, a plant's actual budget, or licensed bulk data.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class OffshoreWindCostBenchmark:
    """Published industry *planning assumptions*, not measured project costs."""

    capex_jpy_per_kw: float
    opex_jpy_per_kw_year: float
    net_capacity_factor: float
    source_url: str
    source_date: str
    evidence_class: str


def load_offshore_cost_snapshot(path: str | Path) -> OffshoreWindCostBenchmark:
    """Load and validate a versioned, offline JWPA/METI cost scenario fixture."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or raw.get("schema_version") != 1:
        raise ValueError("Unsupported cost snapshot schema")
    if raw.get("evidence_class") != "published_industry_assumption":
        raise ValueError("Published planning inputs must not be passed off as observations")
    source = raw["source"]
    values = raw["inputs"]
    if not isinstance(source, dict) or not isinstance(values, dict):
        raise ValueError("Invalid source or inputs object")
    capex = float(values["capex_jpy_per_kw"])
    opex = float(values["opex_jpy_per_kw_year"])
    capacity_factor = float(values["net_capacity_factor"])
    if any(not math.isfinite(x) for x in (capex, opex, capacity_factor)):
        raise ValueError("Input values must be finite")
    if capex < 0 or opex < 0 or not 0 < capacity_factor <= 1:
        raise ValueError("Invalid cost or net capacity factor")
    url = str(source["primary_url"])
    date = str(source["published_date"])
    if not url.startswith("https://www.meti.go.jp/") or len(date) != 10:
        raise ValueError("Unexpected source URL or publication date")
    return OffshoreWindCostBenchmark(
        capex_jpy_per_kw=capex,
        opex_jpy_per_kw_year=opex,
        net_capacity_factor=capacity_factor,
        source_url=url,
        source_date=date,
        evidence_class=raw["evidence_class"],
    )
