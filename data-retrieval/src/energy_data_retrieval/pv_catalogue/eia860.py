"""EIA-860 solar/plant workbook adapter: one record per operating PV plant ID.

The operating PV generators are nested; capacities sum only OP/PV units. Thermal,
storage and non-operating units never inflate PV totals. Raw nonempty plant and
solar workbook fields are preserved as namespaced extensions and phase details.
"""

from __future__ import annotations

import io
import math
from collections import defaultdict
from typing import Any
from zipfile import ZipFile

import pandas as pd

from .catalogue import canonical_json, stable_id


def _clean(value: Any) -> Any:
    if pd.isna(value) or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, str):
        return value.strip()
    if hasattr(value, "item"):
        return value.item()
    return value


def _number(value: Any) -> float | None:
    value = _clean(value)
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Non-finite EIA numeric value")
    return number


def parse_eia860_frames(
    plants: pd.DataFrame, solar: pd.DataFrame, *, source_id: str, retrieved_at: str, year: int
) -> list[dict[str, Any]]:
    """Map official frames, excluding non-OP and non-PV records explicitly.

    Blank values stay null, and a capacity total is null if any component is missing.
    Generator-level dates/angles are never promoted to whole-project attributes.
    """
    required_plants = {"Plant Code", "Plant Name", "State", "County", "Latitude", "Longitude"}
    required_solar = {
        "Plant Code",
        "Generator ID",
        "Status",
        "Prime Mover",
        "Technology",
        "Nameplate Capacity (MW)",
        "DC Net Capacity (MW)",
    }
    if not required_plants <= set(plants) or not required_solar <= set(solar):
        raise ValueError("EIA-860 columns changed; review adapter")
    if plants["Plant Code"].duplicated().any():
        raise ValueError("Duplicate EIA plant IDs")
    plant_lookup = {int(p["Plant Code"]): p for p in plants.to_dict(orient="records")}
    selected = solar[
        (solar["Status"] == "OP")
        & (solar["Prime Mover"] == "PV")
        & (solar["Technology"] == "Solar Photovoltaic")
    ]
    if selected.duplicated(["Plant Code", "Generator ID"]).any():
        raise ValueError("Duplicate EIA generator IDs")
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for generator in selected.to_dict(orient="records"):
        grouped[int(generator["Plant Code"])].append(
            {str(k): _clean(v) for k, v in generator.items()}
        )
    result = []
    for code, generators in sorted(grouped.items()):
        if code not in plant_lookup:
            raise ValueError(f"EIA generator lacks plant metadata: {code}")
        plant = {k: _clean(v) for k, v in plant_lookup[code].items()}
        row: dict[str, Any] = {
            "record_id": stable_id("projects", "EIA", str(code)),
            "entity_type": "projects",
            "name": plant["Plant Name"],
            "country_code": "USA",
            "region": plant["State"],
            "locality": plant["County"],
            "technology": "photovoltaic",
            "status": "operating_pv_generators",
            "source_date": str(year),
            "capacity_basis": "sum of OP/PV generators only; EIA nameplate AC and net DC",
            "external_ids_json": canonical_json({"eia_plant_code": str(code)}),
            "phases_json": canonical_json(
                [
                    {
                        "generator_id": str(g["Generator ID"]),
                        "eia_solar": {k: v for k, v in g.items() if v is not None},
                    }
                    for g in sorted(generators, key=lambda g: str(g["Generator ID"]))
                ]
            ),
            "extensions_json": canonical_json(
                {"eia_plant": {k: v for k, v in plant.items() if v is not None}}
            ),
            "sources": [source_id],
            "field_sources_json": canonical_json({"*": source_id}),
            "quality_status": "official_registry",
            "created_at": retrieved_at,
            "updated_at": retrieved_at,
            "last_verified_at": retrieved_at,
            "notes": "Annual reported snapshot, not live status. PV portion of the EIA plant only.",
        }
        for canonical, native in (
            ("capacity_ac_mw", "Nameplate Capacity (MW)"),
            ("capacity_dc_mw", "DC Net Capacity (MW)"),
        ):
            values = [_number(g[native]) for g in generators]
            if all(value is not None for value in values):
                row[canonical] = round(sum(v for v in values if v is not None), 6)
        lat, lon = _number(plant.get("Latitude")), _number(plant.get("Longitude"))
        if lat is not None and lon is not None:
            row.update(latitude=lat, longitude=lon, location_accuracy="source_reported")
        voltage = _number(plant.get("Grid Voltage (kV)"))
        if voltage is not None and voltage > 0:
            row["grid_voltage_kv"] = voltage
        result.append({k: v for k, v in row.items() if v is not None})
    return result


def parse_eia860_archive(
    content: bytes, *, source_id: str, retrieved_at: str, year: int
) -> list[dict[str, Any]]:
    """Read explicit workbook names from a size-bounded archive, without extracting files."""
    names = [f"2___Plant_Y{year}.xlsx", f"3_3_Solar_Y{year}.xlsx"]
    if len(content) > 100_000_000:
        raise ValueError("EIA archive exceeds size limit")
    with ZipFile(io.BytesIO(content)) as archive:
        if any(archive.getinfo(name).file_size > 50_000_000 for name in names):
            raise ValueError("EIA workbook exceeds size limit")
        plants = pd.read_excel(io.BytesIO(archive.read(names[0])), sheet_name="Plant", header=1)
        solar = pd.read_excel(io.BytesIO(archive.read(names[1])), sheet_name="Operable", header=1)
    return parse_eia860_frames(
        plants, solar, source_id=source_id, retrieved_at=retrieved_at, year=year
    )
