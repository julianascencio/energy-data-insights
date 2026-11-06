"""Stage reviewed Pylontech Force-L1 v2.3 / Force-L2 v2.2 system tables from local PDF text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.pylontech_force import parse_force


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--family", choices=["Force-L1", "Force-L2"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_force(args.input.read_text(), family=args.family)
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
