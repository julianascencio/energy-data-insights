"""Stage a local LEOCH OPzS sheet; no network or canonical writes."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.leoch_opzs import parse_opzs


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse_opzs(args.text.read_text(), args.model)
    with args.output.open("x") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
