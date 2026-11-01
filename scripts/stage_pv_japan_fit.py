"""Stage Japan FIT review candidates, never accepted catalogue records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.japan_fit import stage_fit_review


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--prefecture", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    review = stage_fit_review(
        args.input.read_bytes(),
        sha256=args.sha256,
        source_id=args.source_id,
        snapshot_date=args.snapshot_date,
        prefecture=args.prefecture,
    )
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(review, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    print(f"Held {review['candidate_count']} candidates; accepted 0 records")


if __name__ == "__main__":
    main()
