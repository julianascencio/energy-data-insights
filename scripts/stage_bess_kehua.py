"""Stage local Kehua exact-model HTML panels; no network or catalogue writes."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.kehua import parse_kehua_html


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_kehua_html(args.input.read_bytes(), expected_models=args.models)
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
