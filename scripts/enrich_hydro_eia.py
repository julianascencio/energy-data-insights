"""Reproduce the reviewed EIA hydro enrichment from retained bounded evidence."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.eia import enrich
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("catalogues/hydro"))
    parser.add_argument("--batch", type=Path)
    args = parser.parse_args()
    root = args.root
    batch_path = args.batch or root / "research/eia-2025-0001-0500.json"
    batch = json.loads(batch_path.read_text())
    accepted = {r["record_id"]: r for r in batch["accepted"]}
    for path in sorted((root / "records").rglob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        for i, row in enumerate(rows):
            if row["record_id"] in accepted:
                rows[i] = enrich(
                    row,
                    accepted[row["record_id"]]["inventory"],
                    source_id=batch["source_id"],
                    identity_source_id="wri_usa_identity",
                    now=batch["reviewed_at"],
                )
        text = "".join(canonical_json(row) + "\n" for row in rows)
        if path.read_text() != text:
            path.write_text(text)
    print(f"Applied {len(accepted)} EIA enrichments; no new plant identities")


if __name__ == "__main__":
    main()
