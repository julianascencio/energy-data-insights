"""Read KenGen 2025 statistics with explicit rating and fiscal-year boundaries."""

import copy
import json
import math
import re
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

SOURCE_ID = "kengen-annual-2025-20261106"
NAMES = (
    "Tana",
    "Masinga",
    "Kamburu",
    "Gitaru",
    "Kindaruma",
    "Kiambere",
    "Turkwel",
    "Sondu Miriu",
    "Sang\u2019oro",
    "Sagana",
    "Mesco",
    "Wanjii",
    "Gogo",
)


def parse_statistics(text: str) -> list[dict[str, Any]]:
    """Parse pdftotext -layout output of printed pp. 246 and 249, fail closed.

    Totals and Small Hydros are deliberately excluded: they overlap named plants.
    A dash is missing, never zero. Sold energy and effective capacity retain their
    own fields; neither is substituted for generation or installed capacity.
    """
    result: dict[str, dict[str, Any]] = {}
    for heading, fields, unit, page in (
        (
            "Installed vs Effective Capacity (MW)",
            ("installed_capacity_mw", "effective_capacity_mw"),
            "MW",
            246,
        ),
        ("Units Sent out (GWh)", ("annual_generation_gwh", "sold_energy_gwh"), "GWh", 249),
    ):
        sections = text.split(heading)
        matches = [part.split("\f")[0] for part in sections[1:] if "HYDRO" in part.split("\f")[0]]
        if len(matches) != 1:
            raise ValueError("Expected exactly one hydro statistics page per table")
        section = matches[0]
        if not re.search(r"2025\s+2024\s+2023\s+2022\s+2021", section):
            raise ValueError("Unexpected statistics year order")
        labels = r"Installed\s+Effective" if unit == "MW" else r"Generated\s+Sales"
        if not re.search(r"Power Plant\s+" + labels, section):
            raise ValueError("Unexpected paired statistics column order")
        found = set()
        for line in section.splitlines():
            for name in NAMES:
                match = re.fullmatch(r"\s*" + re.escape(name) + r"\s{2,}(.+?)\s*", line)
                if not match:
                    continue
                if name in found:
                    raise ValueError("Duplicate plant statistics row")
                found.add(name)
                cells = match[1].split()
                if len(cells) != 10:
                    raise ValueError("Expected five paired annual values")
                item = result.setdefault(name, {"source_name": name, "observations": []})
                for i, token in enumerate(cells):
                    value = None if token == "-" else float(token.replace(",", ""))
                    if value is not None and (not math.isfinite(value) or value < 0):
                        raise ValueError("Invalid nonnegative statistics value")
                    year = 2025 - i // 2
                    item["observations"].append(
                        {
                            "field": fields[i % 2],
                            "value": value,
                            "unit": unit,
                            "kind": "reported",
                            "period": f"FY ended {year}-06-30",
                            "boundary": (
                                "Named station; owner statistical table; not current operation"
                            ),
                            "source_id": SOURCE_ID,
                            "locator": (
                                f"Printed p. {page}; {heading}; {name}; {year}; column {i % 2 + 1}"
                            ),
                            "original_value": token,
                            "uncertainty": "Not quantified by publisher",
                        }
                    )
        expected = set(NAMES[:9] if unit == "MW" else NAMES)
        if found != expected:
            raise ValueError("Missing or unexpected named hydro statistics rows")
    return list(result.values())


def enrich_reviewed(existing: dict[str, Any], entry: dict[str, Any], *, now: str) -> dict[str, Any]:
    """Apply an explicit owner/name/UUID crosswalk without overwriting ratings."""
    if (
        existing["record_id"] != entry["record_id"]
        or existing["country_code"] != "KEN"
        or existing["name"] != entry["canonical_name"]
        or existing.get("owner_names") != ["Kenya Electric Generating Company"]
        or entry.get("decision") != "accepted_owner_identity"
    ):
        raise ValueError("Explicit KenGen owner identity review required")
    item = entry["inventory"]
    expected_name = {"Sondu Miru": "Sondu Miriu"}.get(existing["name"], existing["name"])
    if (
        item["source_name"] != expected_name
        or item["source_name"] not in NAMES
        or len(item["observations"]) != 20
    ):
        raise ValueError("Expected reviewed complete station statistics")
    row = copy.deepcopy(existing)
    ext = json.loads(row["extensions_json"])
    evidence = {
        "source_id": SOURCE_ID,
        "source_name": item["source_name"],
        "identity_basis": entry["identity_basis"],
    }
    if "kengen_2025_identity" in ext:
        prior = [o for o in json.loads(row["observations_json"]) if o.get("source_id") == SOURCE_ID]
        if ext["kengen_2025_identity"] != evidence or prior != item["observations"]:
            raise ValueError("Changed owner statistics require conflict review")
        return row
    ext["kengen_2025_identity"] = evidence
    observations = json.loads(row["observations_json"])
    observations.extend(item["observations"])
    fs, ev = json.loads(row["field_sources_json"]), json.loads(row["evidence_json"])
    for field, value in {
        "extensions_json": canonical_json(ext),
        "observations_json": canonical_json(observations),
    }.items():
        row[field] = value
        fs[field] = sorted(set([*fs.get(field, []), SOURCE_ID]))
        ev[field] = {
            "locator": "KenGen 2025 printed pp. 246, 249; per-cell locators in observations_json",
            "confidence": "high",
            "original_value": value,
            "normalization": (
                "Fiscal years; separate installed/effective MW and generated/sold GWh; "
                "historical values preserved"
            ),
        }
    row.update(
        field_sources_json=canonical_json(fs),
        evidence_json=canonical_json(ev),
        sources=sorted(set(row["sources"] + [SOURCE_ID])),
        updated_at=now,
        last_verified_at=now,
    )
    return row
