"""Stage reviewed ATESS BC55NPB or VoltStack rack columns from local layout text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.atess_battery import SOURCE_URLS, parse_battery_table


def main() -> None:
    """Write candidate facts only; canonical upsert requires separate identity review."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--model", choices=sorted(SOURCE_URLS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_battery_table(
        args.input.read_bytes(), model=args.model, source_url=SOURCE_URLS[args.model]
    )
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
