"""Pinned Navarra operating-PV DBF index; explicit reviewed acceptance only."""

from __future__ import annotations

import io
import math
import re
import struct
import zipfile
from collections import Counter
from decimal import Decimal, InvalidOperation
from typing import Any

from .catalogue import canonical_json, stable_id
from .sam import verify_sha256

COLUMNS = [
    "FEATURE",
    "NOMBRE",
    "PROMOTOR",
    "POT_MW",
    "PUESTSERV",
    "EXPEDIENTE",
    "RAIPEE",
    "DIA",
    "EVACUACION",
    "GEOM_AREA",
    "GEOM_PERI",
    "BEGINLIFE",
]


def read_navarra_archive(
    content: bytes, *, sha256: str, layer: str = "operating"
) -> list[dict[str, str]]:
    """Verify original archive, layer-specific rights/definition and DBF framing.

    FEATURE is not unique. PROMOTOR is deliberately discarded before returning
    rows: it may identify a natural person. No coordinates or centroid are derived.
    """
    if layer not in {"operating", "permitting"}:
        raise ValueError("Unknown Navarra layer")
    suffix = "" if layer == "operating" else "Tra"
    title = "Plantas solares fotovoltaicas en " + (
        "servicio" if layer == "operating" else "tramitación"
    )
    expected_columns = (
        COLUMNS
        if layer == "operating"
        else [k for k in COLUMNS if k not in {"PUESTSERV", "RAIPEE"}]
    )
    verify_sha256(content, sha256)
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        if sum(f.file_size for f in archive.infolist()) > 10_000_000:
            raise ValueError("Oversized Navarra archive")
        meta = archive.read("spaSITNAENERGI_Pol_PSolar" + suffix + ".xml").decode("utf-8")
        if not all(
            s in meta
            for s in (
                "CC BY 4.0",
                "suma de las potencias de los paneles",
                title,
            )
        ):
            raise ValueError("Navarra rights or power definition changed")
        data = archive.read("ENERGI_Pol_PSolar" + suffix + ".dbf")
    if len(data) < 33:
        raise ValueError("Truncated Navarra DBF")
    count, header, width = struct.unpack("<IHH", data[4:12])
    if header < 33 or (header - 33) % 32 or header > len(data):
        raise ValueError("Invalid Navarra DBF header")
    columns = []
    for offset in range(32, header - 1, 32):
        descriptor = data[offset : offset + 32]
        columns.append((descriptor[:11].split(b"\0")[0].decode("ascii"), descriptor[16]))
    if [k for k, _ in columns] != expected_columns or sum(w for _, w in columns) + 1 != width:
        raise ValueError("Navarra DBF schema changed")
    if data[header - 1] != 13 or len(data) not in (
        header + count * width,
        header + count * width + 1,
    ):
        raise ValueError("Truncated or unexpected Navarra DBF records")
    rows = []
    for i in range(count):
        record = data[header + i * width : header + (i + 1) * width]
        if record[0] != 32:
            raise ValueError("Deleted/unexpected Navarra row requires review")
        row = {"row_locator": str(i + 1), "source_layer": title}
        offset = 1
        for key, length in columns:
            value = record[offset : offset + length].decode("cp1252").strip()
            if key != "PROMOTOR":
                row[key] = value
            offset += length
        try:
            power = Decimal(row["POT_MW"])
        except InvalidOperation as exc:
            raise ValueError("Invalid Navarra panel power") from exc
        if (
            not math.isfinite(float(power))
            or not power.is_finite()
            or power <= 0
            or not row["NOMBRE"]
        ):
            raise ValueError("Invalid Navarra panel power or identity")
        rows.append(row)
    return rows


def reviewed_navarra_project(
    row: dict[str, str],
    *,
    rows: list[dict[str, str]],
    source_id: str,
    now: str,
    approved_case: str,
) -> dict[str, Any]:
    """Build only a manually approved unique single-case facility.

    Caller must review all incoming and canonical names/IDs/spatial/phase risks.
    Never use FEATURE, generic RAIPEE text or the row number as project identity.
    Normalized operating status/service date and exact location stay unknown.
    """
    case = row["EXPEDIENTE"]
    counts = Counter(r["EXPEDIENTE"] for r in rows)
    if case != approved_case or not re.fullmatch(r"\d+-CE", case) or counts[case] != 1:
        raise ValueError("Unreviewed, repeated or aggregate Navarra case")
    native = {
        "locator": (
            "ENERGI_Pol_PSolarTra.dbf"
            if "tramitación" in row["source_layer"]
            else "ENERGI_Pol_PSolar.dbf"
        )
        + " row "
        + row["row_locator"],
        "case_reference": case,
        "panel_power_mw_printed": row["POT_MW"],
        "power_basis": "sum of panel ratings; not grid/net/export power",
        "service_year_printed": row.get("PUESTSERV", ""),
        "service_year_scope": "Generic dictionary year description; not normalized commissioning",
        "registration_text": row.get("RAIPEE", ""),
        "environmental_declaration": row["DIA"],
        "grid_connection_text": row["EVACUACION"],
        "database_insertion_date": row["BEGINLIFE"],
        "source_layer": row["source_layer"],
        "lifecycle_scope": "Layer classification; effective date per row not verified",
        "privacy": "Promoter omitted; no private owner, address or contact retained",
    }
    return {
        "record_id": stable_id("projects", "ESP", "navarra_case", case),
        "entity_type": "projects",
        "name": row["NOMBRE"],
        "country_code": "ESP",
        "region": "Comunidad Foral de Navarra",
        "technology": "photovoltaic",
        "capacity_dc_mw": float(Decimal(row["POT_MW"])),
        "capacity_basis": "Sum of panel ratings (MW); source definition",
        "external_ids_json": canonical_json({"navarra_case": case}),
        "extensions_json": canonical_json({"navarra": native}),
        "sources": [source_id],
        "field_sources_json": canonical_json({"*": source_id}),
        "quality_status": "reviewed_regional_inventory",
        "created_at": now,
        "updated_at": now,
        "last_verified_at": now,
    }
