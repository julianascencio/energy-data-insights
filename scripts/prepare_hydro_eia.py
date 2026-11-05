"""Prepare an offline EIA hydro evidence batch; canonical records are not modified."""

import argparse
import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path

from energy_data_retrieval.hydro_catalogue import load_records
from energy_data_retrieval.hydro_catalogue.eia import parse_partition, review_partition


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--first", type=int, required=True)
    parser.add_argument("--last", type=int, required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("catalogues/hydro"))
    args = parser.parse_args()
    stamp = datetime.fromisoformat(args.reviewed_at)
    if stamp.tzinfo is None or stamp.year <= args.year:
        parser.error("Review needs a timezone-aware timestamp after the inventory year")
    archive = args.archive.read_bytes()
    if hashlib.sha256(archive).hexdigest() != args.sha256:
        parser.error("Archive checksum mismatch")
    with zipfile.ZipFile(args.archive) as source:
        plants = source.read(f"2___Plant_Y{args.year}.xlsx")
        units = source.read(f"3_1_Generator_Y{args.year}.xlsx")
    source_id = f"eia860-{args.year}-hydro-{args.first}-{args.last}"
    sources = json.loads((args.root / "sources.json").read_text())
    if sources[source_id]["sha256"] != args.sha256 or "wri_usa_identity" not in sources:
        parser.error("Register the reviewed source checksum and identity mapping first")
    items = parse_partition(plants, units, year=args.year, first=args.first, last=args.last)
    batch = {
        "source_id": source_id,
        "reviewed_at": args.reviewed_at,
        "partition": {"first": args.first, "last": args.last, "next_first": args.last + 1},
        **review_partition(
            load_records(args.root),
            items,
            source_id=source_id,
            identity_source_id="wri_usa_identity",
            now=args.reviewed_at,
        ),
        "limitations": (
            f"Accepted units are HY/OP in {args.year}; not live operation. "
            "No fuzzy merges. Capacity aggregation scopes remain unresolved. "
            "Held inventories are evidence for review, not accepted canonical data."
        ),
    }
    text = json.dumps(batch, indent=2) + "\n"
    if args.output.exists() and args.output.read_text() != text:
        parser.error("Refusing to overwrite a different existing review batch")
    args.output.write_text(text)
    print(f"Prepared {len(batch['accepted'])} enrichments / {len(items)} reviewed identities")


if __name__ == "__main__":
    main()
