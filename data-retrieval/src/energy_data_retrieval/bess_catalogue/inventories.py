"""Offline inventory adapters; outputs are candidates requiring scope reconciliation.

EIA rows aggregate operating battery units by plant ID. REPD rows retain planning
reference IDs and must be checked for phases, aliases and revised applications.
Neither adapter overwrites curated records or equates a planned date with COD.
"""

from __future__ import annotations

import io
from collections import defaultdict
from typing import Any
from zipfile import ZipFile

import pandas as pd

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json
from energy_data_retrieval.pv_catalogue.eia860 import _clean, _number

from .catalogue import ADMIN, stable_id

CHEMISTRIES = {
    "LIB": "lithium-ion",
    "FLB": "flow battery (electrolyte unspecified)",
    "PBB": "lead-acid",
    "MAB": "metal-air",
    "NIB": "nickel-based",
    "NAB": "sodium-based",
}


def _finish(row: dict[str, Any], source_id: str, retrieved_at: str) -> dict[str, Any]:
    row = {k: v for k, v in row.items() if v is not None}
    row.update(
        entity_type="projects",
        sources=[source_id],
        quality_status="source_backed",
        created_at=retrieved_at,
        updated_at=retrieved_at,
        last_verified_at=retrieved_at,
    )
    row["field_sources_json"] = canonical_json({k: [source_id] for k in row if k not in ADMIN})
    return row


def _sum_complete(generators: list[dict[str, Any]], column: str) -> float | None:
    values = [_number(g.get(column)) for g in generators]
    if any(v is None for v in values):
        return None
    return round(sum(v for v in values if v is not None), 6)


def _battery(g: dict[str, Any]) -> bool:
    # EIA groups electrochemical capacitors under BA/Batteries; they are outside
    # this catalogue's electrochemical-battery scope. Do not map them to batteries.
    return (
        g["Prime Mover"] == "BA"
        and g["Technology"] == "Batteries"
        and not any(g.get(f"Storage Technology {i}") == "ECC" for i in range(1, 5))
    )


def parse_eia860_frames(
    plants: pd.DataFrame,
    storage: pd.DataFrame,
    *,
    source_id: str,
    retrieved_at: str,
    year: int,
) -> list[dict[str, Any]]:
    """Aggregate OP batteries, retaining other battery units outside the totals.

    Nameplate power is AC per EIA instructions; energy is nameplate (nominal).
    An incomplete component makes the total unknown, not a partial sum. Generator
    operating months/years stay nested; they are not a whole-project COD.
    """
    required = {
        "Plant Code",
        "Generator ID",
        "Status",
        "Prime Mover",
        "Technology",
        "Nameplate Capacity (MW)",
        "Nameplate Energy Capacity (MWh)",
        "Storage Technology 1",
    }
    if not {"Plant Code", "Plant Name", "State", "County"} <= set(plants) or not required <= set(
        storage
    ):
        raise ValueError("EIA-860 columns changed; review adapter")
    if plants["Plant Code"].duplicated().any():
        raise ValueError("Duplicate EIA plant IDs")
    plant_lookup = {int(p["Plant Code"]): p for p in plants.to_dict(orient="records")}
    grouped: dict[int, list[dict[str, Any]]] = defaultdict(list)
    seen = set()
    for original in storage.to_dict(orient="records"):
        g = {str(k): _clean(v) for k, v in original.items()}
        if not _battery(g):
            continue
        key = (int(g["Plant Code"]), str(g["Generator ID"]))
        if key in seen:
            raise ValueError("Duplicate EIA battery generator IDs")
        seen.add(key)
        grouped[key[0]].append(g)
    result = []
    for code, all_units in sorted(grouped.items()):
        generators = [g for g in all_units if g["Status"] == "OP"]
        if not generators:
            continue
        if code not in plant_lookup:
            raise ValueError(f"EIA generator lacks plant metadata: {code}")
        plant = {str(k): _clean(v) for k, v in plant_lookup[code].items()}
        row: dict[str, Any] = {
            "record_id": stable_id("USA", "EIA plant", str(code)),
            "name": plant["Plant Name"],
            "country_code": "USA",
            "region": plant["State"],
            "locality": plant["County"],
            "capacity_scope": (
                "Sum of EIA OP battery generators at this plant ID only; "
                "other technologies and non-OP units excluded"
            ),
            "status": "operational"
            if len(generators) == len(all_units)
            else "partially_operational",
            "status_as_of": f"{year}-12-31",
            "status_date_basis": "reporting_period_end",
            "power_capacity_mw": _sum_complete(generators, "Nameplate Capacity (MW)"),
            "power_basis": "ac",
            "energy_capacity_mwh": _sum_complete(generators, "Nameplate Energy Capacity (MWh)"),
            "energy_basis": "nominal",
            "charging_power_mw": _sum_complete(generators, "Maximum Charge Rate (MW)"),
            "operators": [plant["Utility Name"]] if plant.get("Utility Name") else None,
            "external_ids_json": canonical_json({"eia_plant_code": str(code)}),
            "phases_json": canonical_json(
                [
                    {
                        "generator_id": str(g["Generator ID"]),
                        "included_in_capacity": g["Status"] == "OP",
                        "eia_storage": {k: v for k, v in g.items() if v is not None},
                    }
                    for g in sorted(all_units, key=lambda g: str(g["Generator ID"]))
                ]
            ),
            "extensions_json": canonical_json(
                {
                    "eia_report_year": year,
                    "eia_plant": {k: v for k, v in plant.items() if v is not None},
                }
            ),
            "notes": (
                "Annual reported snapshot, not current availability. Plant IDs may be "
                "subdivisions of a commercial project; reconcile before publication."
            ),
        }
        codes = [g.get(f"Storage Technology {i}") for g in generators for i in range(1, 5)]
        known = sorted({c for c in codes if c is not None})
        if all(g.get("Storage Technology 1") in CHEMISTRIES for g in generators) and all(
            c in CHEMISTRIES for c in known
        ):
            row["chemistry"] = "; ".join(CHEMISTRIES[c] for c in known)
        lat, lon = _number(plant.get("Latitude")), _number(plant.get("Longitude"))
        if lat is not None and lon is not None:
            row.update(
                latitude=lat, longitude=lon, location_accuracy="source_reported_plant_location"
            )
        voltage = _number(plant.get("Grid Voltage (kV)"))
        if voltage is not None and voltage > 0:
            row["grid_voltage_kv"] = voltage
        result.append(_finish(row, source_id, retrieved_at))
    return result


def parse_eia860_archive(
    content: bytes, *, source_id: str, retrieved_at: str, year: int
) -> list[dict[str, Any]]:
    """Read the two explicit workbook members without extracting archive paths."""
    names = [f"2___Plant_Y{year}.xlsx", f"3_4_Energy_Storage_Y{year}.xlsx"]
    if len(content) > 100_000_000:
        raise ValueError("EIA archive exceeds size limit")
    with ZipFile(io.BytesIO(content)) as archive:
        if any(archive.getinfo(name).file_size > 50_000_000 for name in names):
            raise ValueError("EIA workbook exceeds size limit")
        plants = pd.read_excel(io.BytesIO(archive.read(names[0])), sheet_name="Plant", header=1)
        storage = pd.read_excel(io.BytesIO(archive.read(names[1])), sheet_name="Operable", header=1)
    return parse_eia860_frames(
        plants, storage, source_id=source_id, retrieved_at=retrieved_at, year=year
    )


def parse_repd_frame(
    frame: pd.DataFrame, *, source_id: str, retrieved_at: str, published_date: str
) -> list[dict[str, Any]]:
    """Stage operational battery planning records, not automatically unique sites.

    REPD does not report MWh. The applicant/operator label and grid coordinates
    remain native metadata; neither is promoted to ownership or WGS84 location.
    Operational dates remain native, without asserting an exact commercial COD.
    """
    required = {
        "Ref ID",
        "Site Name",
        "Technology Type",
        "Development Status",
        "Installed Capacity (MWelec)",
        "County",
        "Country",
        "Region",
    }
    if not required <= set(frame):
        raise ValueError("REPD columns changed; review adapter")
    if frame["Ref ID"].duplicated().any():
        raise ValueError("Duplicate REPD reference IDs")
    result = []
    for original in frame.to_dict(orient="records"):
        r = {str(k).strip(): _clean(v) for k, v in original.items()}
        if r["Technology Type"] != "Battery" or r["Development Status"] != "Operational":
            continue
        if r["Country"] not in {"England", "Scotland", "Wales", "Northern Ireland"}:
            raise ValueError("Unrecognized REPD country")
        code = str(int(r["Ref ID"]))
        row = {
            "record_id": stable_id("GBR", "REPD", code),
            "name": r["Site Name"],
            "country_code": "GBR",
            "region": r["Region"],
            "locality": r["County"],
            "capacity_scope": (
                "Battery planning-record capacity reported by REPD; "
                "MWh and electrical rating basis unreported"
            ),
            "status": "operational",
            "status_as_of": published_date,
            "status_date_basis": "publication_date",
            "power_capacity_mw": _number(r["Installed Capacity (MWelec)"]),
            "power_basis": "unspecified",
            "configuration": "standalone"
            if r.get("Storage Type") == "Stand-alone Storage"
            else None,
            "external_ids_json": canonical_json({"repd_ref_id": code}),
            "extensions_json": canonical_json(
                {"repd": {k: v for k, v in r.items() if v is not None}}
            ),
            "notes": (
                "REPD release observation, not live availability. Planning entries may overlap; "
                "review proximity, aliases, phases and reapplication IDs before publication. "
                "Native operational date is not asserted as COD."
            ),
        }
        result.append(_finish(row, source_id, retrieved_at))
    return sorted(result, key=lambda row: row["record_id"])


def parse_repd_csv(
    content: bytes, *, source_id: str, retrieved_at: str, published_date: str
) -> list[dict[str, Any]]:
    """Read the registered Windows-1252 REPD export with bounded input size."""
    if len(content) > 50_000_000:
        raise ValueError("REPD file exceeds size limit")
    frame = pd.read_csv(io.BytesIO(content), encoding="cp1252", low_memory=False)
    return parse_repd_frame(
        frame, source_id=source_id, retrieved_at=retrieved_at, published_date=published_date
    )
