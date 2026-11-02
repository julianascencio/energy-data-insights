"""Stage a downloaded ODRÉ battery partition; do not import or merge identities."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.odre import stage_odre_batteries


def main() -> None:
    """Write review candidates from original JSON bytes and reporting date."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--snapshot-date", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    candidates = stage_odre_batteries(args.input.read_bytes(), snapshot_date=args.snapshot_date)
    args.output.write_text(json.dumps(candidates, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
