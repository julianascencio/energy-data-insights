"""Stage checksum-pinned Catalonia PV observations for manual identity review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.catalonia import stage_catalonia_review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--metadata-sha256", required=True)
    parser.add_argument("--expected-rows", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    staged = stage_catalonia_review(
        args.input.read_bytes(),
        args.metadata.read_bytes(),
        sha256=args.sha256,
        metadata_sha256=args.metadata_sha256,
        expected_rows=args.expected_rows,
    )
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(staged, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Staged {staged['grouped_candidates']} candidates; zero automatically accepted")


if __name__ == "__main__":
    main()
