"""Stage checksum-pinned inventory candidates for review; never edit the catalogue.

Candidate rows can overlap existing commercial projects or one another. Compare
external IDs, coordinates, names and phase scope before accepting any record.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.catalogue import validate_record
from energy_data_retrieval.bess_catalogue.inventories import parse_eia860_archive, parse_repd_csv
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json
from energy_data_retrieval.pv_catalogue.sam import verify_sha256


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("provider", choices=["eia860", "repd"])
    parser.add_argument("input", type=Path)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--root", type=Path, default=Path("catalogues/bess"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    sources = json.loads((args.root / "sources.json").read_text())
    source = sources[args.source_id]
    content = args.input.read_bytes()
    verify_sha256(content, source["sha256"])
    common = {"source_id": args.source_id, "retrieved_at": source["retrieved_at"]}
    if args.provider == "eia860":
        rows = parse_eia860_archive(content, year=source["report_year"], **common)
    else:
        rows = parse_repd_csv(content, published_date=source["published_date"], **common)
    for row in rows:
        validate_record(row, sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents accidental replacement of a reviewed batch.
    with args.output.open("x", encoding="utf-8") as output:
        output.writelines(canonical_json(row) + "\n" for row in rows)
    print(f"Staged {len(rows)} candidates. Review overlap and phase scope before importing.")


if __name__ == "__main__":
    main()
