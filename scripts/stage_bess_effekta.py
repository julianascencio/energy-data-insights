"""Stage EFFEKTA BTL specification candidates from local pdftotext -layout output."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.effekta import SOURCE_URL, parse_btl_table


def main() -> None:
    """Write candidates for manual identity and edition review, without importing."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_btl_table(args.input.read_bytes(), source_url=SOURCE_URL)
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
