"""Stage local TAB OGi PDF text; no network or canonical writes."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.tab_ogi import parse_models


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_models(args.text.read_text())
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
