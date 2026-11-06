"""Stage a reviewed local Hubble warranty; never fetch or write catalogue records."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.hubble_warranty import SCOPES, parse_warranty


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--scope", required=True, choices=SCOPES)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = parse_warranty(args.input.read_text(), scope=args.scope)
    with args.output.open("x") as output:
        json.dump(result, output, indent=2)
        output.write("\n")


if __name__ == "__main__":
    main()
