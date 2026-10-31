"""Import a downloaded, registered EIA-860 archive into the PV catalogue.

Before accepting a new source, reconcile its plant IDs with existing projects.
Conflicting populated fields are quarantined by the catalogue upsert API.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue import load_records, upsert_records, write_records
from energy_data_retrieval.pv_catalogue.eia860 import parse_eia860_archive
from energy_data_retrieval.pv_catalogue.sam import verify_sha256


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--now", required=True)
    parser.add_argument("--root", type=Path, default=Path("catalogues/pv"))
    parser.add_argument("--conflicts", type=Path, required=True)
    args = parser.parse_args()
    sources = json.loads((args.root / "sources.json").read_text())
    content = args.archive.read_bytes()
    verify_sha256(content, sources[args.source_id]["sha256"])
    incoming = parse_eia860_archive(
        content, source_id=args.source_id, retrieved_at=args.now, year=args.year
    )
    existing = load_records(args.root)
    # Reuse reviewed EIA mappings, including the Topaz launch reconciliation.
    crosswalk = {}
    for row in existing:
        ids = json.loads(row.get("external_ids_json", "{}"))
        if "eia_plant_code" in ids:
            if ids["eia_plant_code"] in crosswalk:
                raise ValueError("Duplicate EIA crosswalk")
            crosswalk[ids["eia_plant_code"]] = row["record_id"]
    for row in incoming:
        code = json.loads(row["external_ids_json"])["eia_plant_code"]
        if code in crosswalk:
            row["record_id"] = crosswalk[code]
    rows, conflicts = upsert_records(existing, incoming, now=args.now)
    write_records(args.root, rows)
    args.conflicts.parent.mkdir(parents=True, exist_ok=True)
    args.conflicts.write_text(json.dumps(conflicts, indent=2) + "\n")
    print(f"Read {len(incoming)} PV plants; {len(conflicts)} records require review")


if __name__ == "__main__":
    main()
