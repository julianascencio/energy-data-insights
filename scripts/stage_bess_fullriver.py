"""Stage exact selected Fullriver HTML cards offline; no automatic import."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.fullriver import parse_cards


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse_cards(args.input.read_bytes(), expected_models=args.models)
    with args.output.open("x") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
