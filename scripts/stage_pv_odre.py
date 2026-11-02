"""Reproduce a reviewed ODRE batch offline; emits JSONL for catalogue upsert."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records
from energy_data_retrieval.pv_catalogue.odre import read_odre_json, reviewed_odre_records


def main() -> None:
    """Require two pinned source exports and a reviewed acceptance ledger."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--identities", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, default=Path("catalogues/pv"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    sources = json.loads((args.catalogue / "sources.json").read_text())
    source = sources[review["source_id"]]
    if review["source_sha256"] != source["sha256"]:
        raise ValueError("Review/source revision mismatch; re-review changed bytes")
    rows = read_odre_json(args.input.read_bytes(), sha256=review["source_sha256"])
    identities = read_odre_json(
        args.identities.read_bytes(), sha256=review["identity_sha256"], identities_only=True
    )
    # Existing accepted EICs are omitted solely for idempotent re-staging; all other
    # country records remain in the alias screen. Upsert resolves IDs without churn.
    accepted = set(review["accepted_eics"])
    all_existing = load_records(args.catalogue)
    eic_lookup = {}
    for row in all_existing:
        eic = json.loads(row.get("external_ids_json", "{}")).get("odre_eic")
        if eic:
            if eic in eic_lookup:
                raise ValueError(f"Duplicate existing ODRE crosswalk: {eic}")
            eic_lookup[eic] = row["record_id"]
    existing = [
        r
        for r in all_existing
        if json.loads(r.get("external_ids_json", "{}")).get("odre_eic") not in accepted
    ]
    incoming = reviewed_odre_records(
        rows,
        identities,
        reviewed_ids=accepted,
        existing=existing,
        source_id=review["source_id"],
        retrieved_at=source["retrieved_at"],
        snapshot_date=review["snapshot_date"],
        minimum_kw=review.get("minimum_kw", 10000),
        maximum_kw=review.get("maximum_kw"),
    )
    with args.output.open("x", encoding="utf-8") as stream:
        for row in incoming:
            eic = json.loads(row["external_ids_json"])["odre_eic"]
            if eic in eic_lookup:
                row["record_id"] = eic_lookup[eic]
            stream.write(canonical_json(row) + "\n")
    print(f"Staged {len(incoming)} reviewed records; acceptance requires upsert and validation.")


if __name__ == "__main__":
    main()
