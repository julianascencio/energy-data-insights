"""Reproduce a reviewed REPD batch offline; emits JSONL for the catalogue upsert CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records
from energy_data_retrieval.pv_catalogue.repd import read_repd_csv, reviewed_repd_records


def main() -> None:
    """Require pinned bytes and a reviewed acceptance ledger; never fetch implicitly."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, default=Path("catalogues/pv"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    sources = json.loads((args.catalogue / "sources.json").read_text())
    source = sources[review["source_id"]]
    if review["source_sha256"] != source["sha256"]:
        raise ValueError("Review/source revision mismatch; re-review changed bytes")
    rows = read_repd_csv(args.input.read_bytes(), sha256=source["sha256"])
    incoming = reviewed_repd_records(
        rows,
        reviewed_ids=set(review["accepted_ref_ids"]),
        source_id=review["source_id"],
        retrieved_at=source["retrieved_at"],
        snapshot_date=review["snapshot_date"],
    )
    existing = load_records(args.catalogue)
    by_ref = {}
    for row in existing:
        ref = json.loads(row.get("external_ids_json", "{}")).get("repd_ref_id")
        if ref:
            if ref in by_ref:
                raise ValueError(f"Existing duplicate REPD identity: {ref}")
            by_ref[ref] = row["record_id"]
    for row in incoming:
        ref = json.loads(row["external_ids_json"])["repd_ref_id"]
        if ref in by_ref:
            row["record_id"] = by_ref[ref]
        matches = [
            old
            for old in existing
            if old.get("country_code") == "GBR"
            and old["record_id"] != row["record_id"]
            and row["name"].casefold()
            in [name.casefold() for name in [old["name"], *old.get("aliases", [])]]
        ]
        if matches:
            raise ValueError(f"Existing name/alias requires explicit crosswalk: {row['name']}")
    with args.output.open("x", encoding="utf-8") as stream:
        for row in sorted(incoming, key=lambda item: item["record_id"]):
            stream.write(canonical_json(row) + "\n")
    print(f"Staged {len(incoming)} reviewed records; acceptance requires upsert and validation.")


if __name__ == "__main__":
    main()
