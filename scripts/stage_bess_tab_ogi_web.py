"""Stage locally captured TAB OGi td/th text, preserving blanks; no network writes."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.tab_ogi_web import parse_table_cells


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cells", type=Path, required=True, help="JSON list of td/th text in DOM order"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cells = json.loads(args.cells.read_text())
    if not isinstance(cells, list) or not all(isinstance(c, str) for c in cells):
        raise ValueError("Expected a JSON list of strings, including empty cells")
    rows = parse_table_cells(cells)
    with args.output.open("x") as handle:
        handle.write(json.dumps(rows, indent=2) + "\n")


if __name__ == "__main__":
    main()
