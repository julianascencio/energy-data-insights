"""Stage the reviewed EA status table from local HTML; no canonical writes."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.nz_status import parse_ea_status_html


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = parse_ea_status_html(args.input.read_bytes())
    args.output.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
