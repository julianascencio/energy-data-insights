"""Replay reviewed Madrid municipal PV rows against a pinned baseline catalogue."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records
from energy_data_retrieval.pv_catalogue.madrid import read_madrid_csv, reviewed_madrid_records


def main() -> None:
    """Require exact source bytes and an explicit sequence allowlist."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--review", type=Path, required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = json.loads(args.review.read_text())
    sources = json.loads((args.catalogue / "sources.json").read_text())
    if sources[review["source_id"]]["sha256"] != review["source_sha256"]:
        raise ValueError("Madrid review/source revision mismatch")
    rows = read_madrid_csv(args.input.read_bytes(), sha256=review["source_sha256"])
    records = reviewed_madrid_records(
        rows,
        reviewed_sequences=set(review["accepted_sequences"]),
        existing=load_records(args.catalogue),
        source_id=review["source_id"],
        snapshot_date=review["snapshot_date"],
    )
    with args.output.open("x", encoding="utf-8") as stream:
        for row in records:
            stream.write(canonical_json(row) + "\n")
    print(f"Staged {len(records)} reviewed municipal PV records; upsert/validation required.")


if __name__ == "__main__":
    main()
