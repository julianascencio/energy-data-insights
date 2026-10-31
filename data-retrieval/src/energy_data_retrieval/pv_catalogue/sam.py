"""Loss-aware importer for pinned SAM CEC module and inverter CSV libraries.

These are reference/model libraries, not proof of current certification, stock,
or country availability. Duplicate model identities are quarantined in full.
"""

from __future__ import annotations

import csv
import hashlib
import io
import math
from collections import Counter
from typing import Any

from .catalogue import canonical_json, stable_id

MODULE_MAP = {
    "Technology": "technology",
    "STC": "pmax_stc_w",
    "PTC": "ptc_w",
    "A_c": "area_m2",
    "Length": "length_m",
    "Width": "width_m",
    "N_s": "cells_in_series",
    "I_sc_ref": "isc_a",
    "V_oc_ref": "voc_v",
    "I_mp_ref": "imp_a",
    "V_mp_ref": "vmp_v",
    "alpha_sc": "alpha_isc_a_per_c",
    "beta_oc": "beta_voc_v_per_c",
    "T_NOCT": "noct_c",
    "a_ref": "cec_a_ref_v",
    "I_L_ref": "cec_il_ref_a",
    "I_o_ref": "cec_io_ref_a",
    "R_s": "cec_rs_ohm",
    "R_sh_ref": "cec_rsh_ref_ohm",
    "Adjust": "cec_adjust_pct",
    "gamma_pmp": "gamma_pmax_pct_per_c",
    "Version": "source_release",
    "Date": "source_date",
}
INVERTER_MAP = {
    "Vac": "vac_rated_v",
    "Pso": "startup_power_w",
    "Paco": "pac_rated_w",
    "Pdco": "pdc_rated_w",
    "Vdco": "vdc_rated_v",
    "C0": "sandia_c0_per_w",
    "C1": "sandia_c1_per_v",
    "C2": "sandia_c2_per_v",
    "C3": "sandia_c3_per_v",
    "Pnt": "standby_power_w",
    "Vdcmax": "vdc_max_v",
    "Idcmax": "idc_max_a",
    "Mppt_low": "mppt_min_v",
    "Mppt_high": "mppt_max_v",
    "CEC_Date": "source_date",
}
TEXT_COLUMNS = {"Technology", "Version", "Date", "CEC_Date"}


def parse_sam_csv(
    content: str, *, entity_type: str, source_id: str, retrieved_at: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse the SAM three-header-line format; return accepted and quarantined rows."""
    if entity_type not in {"modules", "inverters"}:
        raise ValueError("SAM supports modules and inverters")
    mapping = MODULE_MAP if entity_type == "modules" else INVERTER_MAP
    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames or not {"Name", *mapping} <= set(reader.fieldnames):
        raise ValueError("SAM CSV header changed; update the explicit adapter first")
    rows = list(reader)
    if len(rows) < 2 or rows[0]["Name"] != "Units" or rows[1]["Name"] != "[0]":
        raise ValueError("Missing SAM unit/variable metadata rows")
    rows = rows[2:]
    counts = Counter(r["Name"] for r in rows)
    accepted, rejected = [], []
    for line, raw in enumerate(rows, start=4):
        if counts[raw["Name"]] > 1:
            rejected.append(
                {
                    "source_id": source_id,
                    "line": line,
                    "reason": "duplicate_model_identity",
                    "raw": raw,
                }
            )
            continue
        if entity_type == "modules":
            manufacturer = raw["Manufacturer"].strip()
            model = raw["Name"].removeprefix(manufacturer).strip()
        else:
            manufacturer, separator, model = raw["Name"].partition(":")
            if not separator:
                rejected.append(
                    {
                        "source_id": source_id,
                        "line": line,
                        "reason": "ambiguous_manufacturer",
                        "raw": raw,
                    }
                )
                continue
            manufacturer, model = manufacturer.strip(), model.strip()
        row: dict[str, Any] = {
            "record_id": stable_id(entity_type, manufacturer, model),
            "entity_type": entity_type,
            "name": raw["Name"],
            "manufacturer": manufacturer,
            "model": model,
            "market_scope": "CEC/SAM reference library; market availability unverified",
            "quality_status": "reference_library",
            "sources": [source_id],
            "field_sources_json": canonical_json({"*": source_id}),
            "created_at": retrieved_at,
            "updated_at": retrieved_at,
            "last_verified_at": retrieved_at,
        }
        for src, dest in mapping.items():
            value = raw[src].strip()
            if value.lower() in {"", "nan", "n/a"}:
                continue
            if src in TEXT_COLUMNS:
                row[dest] = value
            else:
                number = float(value)
                if not math.isfinite(number):
                    raise ValueError(f"Non-finite SAM value at line {line}: {src}")
                if src == "N_s" and not number.is_integer():
                    raise ValueError("Non-integral cell count")
                row[dest] = int(number) if src == "N_s" else number
        bools = (
            {"Bifacial": "bifacial", "BIPV": "bipv"}
            if entity_type == "modules"
            else {"CEC_hybrid": "hybrid"}
        )
        for src, dest in bools.items():
            value = raw.get(src, "").strip()
            if value in {"0", "N", "1", "Y"}:
                row[dest] = value in {"1", "Y"}
            elif value and value.lower() != "nan":
                raise ValueError(f"Unknown boolean: {src}={value}")
        extra = {
            k: v
            for k, v in raw.items()
            if k and k not in {"Name", "Manufacturer", *mapping, *bools} and v
        }
        if extra:
            row["extensions_json"] = canonical_json({"sam": extra})
        accepted.append(row)
    return accepted, rejected


def verify_sha256(content: bytes, expected: str) -> None:
    """Fail closed when a pinned download does not match the source registry."""
    if hashlib.sha256(content).hexdigest() != expected:
        raise ValueError("Source checksum mismatch")
