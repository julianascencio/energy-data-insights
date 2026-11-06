"""Stage Force-H1-V2 tables exported from PDF pages 11-12 with pdfplumber."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.pylontech_hv import parse_h1_v2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tables", type=Path, help="JSON array of two raw tables, not documents")
    parser.add_argument("--revision", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_h1_v2(json.loads(args.tables.read_text()), revision=args.revision)
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
