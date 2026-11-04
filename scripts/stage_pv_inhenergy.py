"""Replay checksum-pinned, manually reviewed SI tables; stage, never directly ingest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, stable_id
from energy_data_retrieval.pv_catalogue.inhenergy import read_inhenergy_layout


def stage(raw: Path, review: dict) -> list[dict]:
    """Verify original bytes, parse exact columns and apply reviewed cell mappings."""
    result = []
    for table in review["tables"]:
        path = raw / table["file"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != table["capture"]["sha256"]:
            raise ValueError(f"Source checksum changed: {table['file']}")
        full_layout = subprocess.run(
            ["pdftotext", "-layout", str(path), "-"], check=True, capture_output=True, text=True
        ).stdout
        if "INHENERGY CO., LTD." not in full_layout:
            raise ValueError("Publisher marker missing from original PDF")
        layout = subprocess.run(
            [
                "pdftotext",
                "-layout",
                "-r",
                "72",
                "-x",
                "590",
                "-y",
                "0",
                "-W",
                "601",
                "-H",
                "808",
                str(path),
                "-",
            ],
            check=True,
            capture_output=True,
            text=True,
        ).stdout
        parsed = read_inhenergy_layout("INHENERGY CO., LTD.\n" + layout, models=table["models"])
        for i, values in enumerate(parsed):
            model = str(values["model"])
            source = table["source_id"]
            native = {
                k: v
                for k, v in values.items()
                if k not in {"model", "pac_rated_w", "output_current_max_a", "vdc_max_v"}
            }
            native.update(
                source_id=source,
                pdf_page=1,
                row_scope="Exact model column; input, AC output, general data and features",
                standard_warranty_condition=(
                    "5 years (standard); brochure statement, eligibility not independently verified"
                ),
                temperature_range_c=[-25, 60],
                maximum_altitude_m=4000,
                topology="Transformerless",
                thdi_bound={"value_pct": 3, "operator": "<", "condition": "Nominal Output"},
                axis_mapping="Native L/W/H retained without remapping to canonical width/depth",
                mppt_scope=(
                    "table_* cells describe the whole source row, not a per-model assignment. "
                    "Per-MPPT values are unsummed. Canonical MPPT/cooling overrides are "
                    "manually reviewed; conflicts in research ledger"
                ),
            )
            row = {
                "record_id": stable_id("inverters", review["manufacturer"], model),
                "entity_type": "inverters",
                "manufacturer": review["manufacturer"],
                "name": f"INHENERGY {model}",
                "model": model,
                "pac_rated_w": values["pac_rated_w"],
                "vdc_max_v": values["vdc_max_v"],
                "output_current_max_a": values["output_current_max_a"],
                "vac_rated_v": table["vac_rated_v"],
                "efficiency_max_pct": table["efficiency_max_pct"],
                "efficiency_euro_pct": table["efficiency_euro_pct"],
                "ip_rating": "IP65",
                "dc_switch": True,
                "operating_temperature_min_c": -25,
                "operating_temperature_max_c": 60,
                "product_warranty_years": 5,
                "product_url": table["product_url"],
                "datasheet_url": table["capture"]["url"],
                "source_release": table["printed_revision"],
                "sources": [source],
                "field_sources_json": canonical_json({"*": source}),
                "quality_status": "primary_source_extract",
                "extensions_json": canonical_json(native),
                "notes": (
                    "Exact OEM column; optional communications/warranty, inequalities and "
                    "current boundaries qualified in extensions. Conflicts remain in review. "
                    "No certification eligibility or project assignment inferred."
                ),
                **{k: review["now"] for k in ["created_at", "updated_at", "last_verified_at"]},
            }
            for field, value in [
                ("weight_kg", table["weights_kg"][i]),
                ("mppt_count", table["mppt_counts"][i]),
                ("cooling_method", table["cooling_methods"][i]),
            ]:
                if value is not None:
                    row[field] = value
            result.append(row)
    if len({r["record_id"] for r in result}) != len(result):
        raise ValueError("Repeated incoming equipment identity")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-dir", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = stage(args.raw_dir, json.loads(args.review.read_text()))
    with args.output.open("x") as stream:
        stream.write("".join(canonical_json(r) + "\n" for r in rows))
    print(f"Staged {len(rows)} reviewed exact models; no catalogue mutation")
