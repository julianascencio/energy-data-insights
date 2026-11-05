"""Stage local TAB OPzS PDF text; no downloads or canonical mutations."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.tab_opzs import parse_blocks, parse_cells


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partition", choices=["cells", "blocks"], default="cells")
    args = parser.parse_args()
    rows = (parse_cells if args.partition == "cells" else parse_blocks)(args.text.read_text())
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
