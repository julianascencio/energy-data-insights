"""Stage reviewed exact Fullriver p2 conditions from local layout text."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.fullriver import (
    parse_charging_conditions,
    parse_small_battery_sheet,
    parse_terminal_case,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--model", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-small-unit", action="store_true")
    parser.add_argument("--include-terminal-case", action="store_true")
    args = parser.parse_args()
    row = parse_charging_conditions(args.input.read_text(), model=args.model)
    if args.include_small_unit:
        row["individual_sheet"] = parse_small_battery_sheet(
            args.input.read_text(), model=args.model
        )
    if args.include_terminal_case:
        row["terminal_case"] = parse_terminal_case(args.input.read_text(), model=args.model)
    with args.output.open("x") as handle:
        handle.write(json.dumps(row, indent=2) + "\n")


if __name__ == "__main__":
    main()
