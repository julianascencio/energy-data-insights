"""Stage four Cook Islands observations; identities and conflicts require review."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.adb_pacific import parse_cook_outer_islands


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_cook_outer_islands(args.input.read_text())
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
