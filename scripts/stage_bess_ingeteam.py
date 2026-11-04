"""Stage local Ingeteam PDF layout text without importing canonical records."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.ingeteam import parse_converter_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--series", choices=["M", "C", "350"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_converter_text(args.input.read_bytes(), args.series)
    args.output.write_text(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
