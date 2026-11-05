"""Stage visually reviewed OEM columns with explicit revision and unit boundaries.

This is a transcription adapter, not OCR. Original bytes must match the review;
model lists are copied from table headers, never expanded from platform ranges.
"""

from __future__ import annotations

import copy
import hashlib
import math
from typing import Any

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json

from .catalogue import stable_id
from .gppd import evidence_record

REFERENCE_IDS = ("windey_english_brochure_202206",)
SCALARS = (
    "rated_power_kw",
    "rotor_diameter_m",
    "blade_length_m",
    "blade_count",
    "cut_in_m_s",
    "rated_wind_speed_m_s",
)


def stage_tables(
    review: dict[str, Any], original: bytes, existing: list[dict[str, Any]], *, now: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return new models and explicit holds for existing configurations.

    Generator RPM is never rotor RPM, converter kVA is never turbine kW,
    and option ranges never become a scalar or a synthetic configuration.
    Existing identities require a separate revision review before enrichment.
    """
    if hashlib.sha256(original).hexdigest() != review["sha256"]:
        raise ValueError("Original OEM checksum mismatch")
    if not review.get("revision") or not review.get("source_id"):
        raise ValueError("OEM revision and source are required")
    prior = {(r.get("manufacturer"), r.get("model")) for r in existing}
    result, ledger = [], []
    seen: set[str] = set()
    pages: set[int] = set()
    for table in review["tables"]:
        page = table["pdf_page"]
        if type(page) is not int or page < 1 or page in pages:
            raise ValueError("Duplicate or invalid OEM page")
        pages.add(page)
        models = [c["model"] for c in table["columns"]]
        if not models or models != table["expected_models"]:
            raise ValueError("Incomplete or reordered OEM columns")
        for column, raw in enumerate(table["columns"], 1):
            model = raw["model"]
            if not model or model in seen:
                raise ValueError("Duplicate or missing exact model")
            seen.add(model)
            for field in SCALARS:
                value = raw[field]
                if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                    raise ValueError("Invalid explicit OEM scalar")
            # Component ratings have their own units and boundaries. Validate
            # optional observations without promoting them to turbine scalars.
            for field in (
                "generator_power_kw",
                "generator_voltage_v",
                "generator_rated_speed_rpm",
                "single_blade_mass_t",
                "hub_mass_t",
                "nacelle_mass_t",
            ):
                value = raw.get(field)
                if value is not None and (
                    type(value) not in (int, float) or not math.isfinite(value) or value <= 0
                ):
                    raise ValueError("Invalid OEM component quantity")
            for field, size in (
                ("converter_power_kva_grid_turbine", 2),
                ("converter_current_a_grid_turbine", 2),
                ("hub_dimensions_m", 3),
                ("nacelle_dimensions_m", 3),
            ):
                values = raw.get(field)
                if values is not None and (
                    not isinstance(values, list)
                    or len(values) != size
                    or any(
                        type(v) not in (int, float) or not math.isfinite(v) or v <= 0
                        for v in values
                    )
                ):
                    raise ValueError("Invalid OEM component vector")
            for field in (
                "cut_out_range_m_s",
                "hub_height_range_m",
                "converter_frequency_range_hz",
            ):
                values = raw[field]
                if (
                    len(values) != 2
                    or any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
                    or not 0 < values[0] <= values[1]
                ):
                    raise ValueError("Invalid OEM option range")
            locator = (
                f"PDF page {page}; printed {table['printed_pages']}; model column {column}: {model}"
            )
            if ("Windey", model) in prior:
                ledger.append(
                    dict(
                        model=model,
                        decision="existing_revision_review",
                        locator=locator,
                        observation=raw,
                    )
                )
                continue
            variant = review["revision"]
            ext = dict(
                oem_table_observations=[
                    dict(
                        source_id=review["source_id"],
                        locator=locator,
                        revision=variant,
                        values=copy.deepcopy(raw),
                    )
                ],
                air_density_kg_m3=None,
                operating_mode=None,
                restart_speed_m_s=None,
                certification_identifier=None,
                warranty_years=None,
                design_life_years=None,
                numerical_curves=None,
                exact_component_models=None,
                installed_project_configuration=None,
                completeness=(
                    "Partial published configuration; ranges are options, not installed values"
                ),
                performance_status="OEM specifications; not independently validated performance",
            )
            values = dict(
                record_id=stable_id("equipment", "Windey", model, variant),
                entity_type="equipment",
                record_scope="model",
                name=f"Windey {model}",
                manufacturer="Windey",
                model=model,
                variant=variant,
                source_revision=variant,
                equipment_category="wind_turbine",
                capacity_scope=(
                    "Exact brochure model; installed revision and project application unknown"
                ),
                rated_power_conditions=(
                    "OEM nominal turbine rating; density and operating mode unspecified"
                ),
                extensions_json=canonical_json(ext),
                **{k: raw[k] for k in SCALARS},
                notes=(
                    "Original units retained in dated table observation. "
                    "No independent performance validation."
                ),
            )
            row = evidence_record(values, source_id=review["source_id"], now=now, locator=locator)
            result.append(row)
            ledger.append(
                dict(model=model, record_id=row["record_id"], decision="addition", locator=locator)
            )
    return result, ledger
