"""Reproduce the reviewed IHA hydro enrichment from retained bounded evidence."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.iha import enrich
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    root = Path("catalogues/hydro")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--batch", type=Path, default=root / "research/iha-india-2019-0001-0100.json"
    )
    batch = json.loads(parser.parse_args().batch.read_text())
    accepted = {r["record_id"]: r for r in batch["accepted"]}
    for path in sorted((root / "records").rglob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        for i, row in enumerate(rows):
            if row["record_id"] in accepted:
                rows[i] = enrich(
                    row,
                    accepted[row["record_id"]]["inventory"],
                    source_id=batch["source_id"],
                    reviewed_record_id=row["record_id"],
                    now=batch["reviewed_at"],
                )
        text = "".join(canonical_json(row) + "\n" for row in rows)
        if path.read_text() != text:
            path.write_text(text)
    print(f"Applied {len(accepted)} IHA enrichments; no new plant identities")


if __name__ == "__main__":
    main()
