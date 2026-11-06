"""Stage the reviewed DCCEEW location partition from local attributed reader text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.dcceew_community import parse_community_tables


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = parse_community_tables(args.input.read_text())
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
