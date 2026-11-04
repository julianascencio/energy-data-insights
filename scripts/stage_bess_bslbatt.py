"""Stage reviewed BSLBATT station specifications from local pdftotext -layout output."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.bslbatt import SOURCE_URLS, parse_station_table


def main() -> None:
    """Write candidate facts; never modify canonical catalogue records."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--family", choices=sorted(SOURCE_URLS), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_station_table(
        args.input.read_bytes(), family=args.family, source_url=SOURCE_URLS[args.family]
    )
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
