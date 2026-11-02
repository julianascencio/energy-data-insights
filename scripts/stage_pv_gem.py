"""Reproduce a checksum-pinned, reviewed GEM project batch offline."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records
from energy_data_retrieval.pv_catalogue.gem import read_gem_workbook, stage_gem_projects
from energy_data_retrieval.pv_catalogue.gem_batches import select_reviewed_gem_batch


def main() -> None:
    """Require the registered source and exact accepted-identity digest."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, default=Path("catalogues/pv"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch", type=int, help="Export only this reviewed publication batch")
    parser.add_argument("--summary", type=Path, help="Complete batch ledger; required with --batch")
    args = parser.parse_args()
    if (args.batch is None) != (args.summary is None):
        parser.error("--batch and --summary must be supplied together")
    review = json.loads(args.review.read_text())
    source = json.loads((args.catalogue / "sources.json").read_text())[review["source_id"]]
    if source["sha256"] != review["sha256"]:
        raise ValueError("Source/review mismatch")
    phases = read_gem_workbook(args.input.read_bytes(), sha256=review["sha256"])
    # Permit replay of the accepted snapshot while screening all other identities.
    existing = [r for r in load_records(args.catalogue) if review["source_id"] not in r["sources"]]
    rows, _held = stage_gem_projects(
        phases,
        existing=existing,
        country_codes=review["country_codes"],
        source_id=review["source_id"],
        now=source["retrieved_at"],
    )
    digest = hashlib.sha256("\n".join(sorted(r["record_id"] for r in rows)).encode()).hexdigest()
    if digest != review["accepted_ids_sha256"]:
        raise ValueError("Accepted identities changed; re-review overlaps before import")
    if args.batch is not None:
        rows = select_reviewed_gem_batch(
            rows, review=review, summary=json.loads(args.summary.read_text()), batch=args.batch
        )
    with args.output.open("x") as out:
        for row in rows:
            out.write(canonical_json(row) + "\n")
    print(f"Reproduced {len(rows)} reviewed GEM project records")


if __name__ == "__main__":
    main()
